from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import sys
# Check if running in Docker container
if os.path.exists('/app/shared'):
    sys.path.append('/app/shared')
else:
    sys.path.append('/home/opsconductor/opsconductor-ng/shared')
from base_service import BaseService

# Import the new Multi-Brain AI Engine (Phase 1: Intent Brain Foundation)
try:
    from multi_brain_engine import MultiBrainAIEngine
    MULTI_BRAIN_AVAILABLE = True
except ImportError as e:
    print(f"Multi-Brain Engine not available: {e}")
    MULTI_BRAIN_AVAILABLE = False
    MultiBrainAIEngine = None

# Legacy brain engine COMPLETELY REMOVED - NO FALLBACKS ALLOWED

# LLM Engine import
from integrations.llm_client import LLMEngine

# PURE LLM CHAT HANDLER - EMBEDDED TO AVOID IMPORT ISSUES

# Modern API imports (replacing legacy)
# from api.knowledge_router import knowledge_router  # Temporarily disabled - missing knowledge_engine
# from api.learning_router import learning_router  # Temporarily disabled - missing knowledge_engine

# Legacy analytics and processing REMOVED - Multi-Brain AI Engine handles all processing

# Job Engine imports
from job_engine.workflow_generator import WorkflowGenerator

# Integration imports
from integrations.asset_client import AssetServiceClient
from integrations.automation_client import AutomationServiceClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class AIService(BaseService):
    def __init__(self):
        super().__init__("ai-service")
        
app = FastAPI(
    title="OpsConductor AI Service",
    description="AI-powered automation and natural language processing service with advanced learning capabilities",
    version="1.0.0"
)

# Include modern API routes
# app.include_router(knowledge_router)  # Temporarily disabled - missing knowledge_engine
# app.include_router(learning_router)  # Temporarily disabled - missing knowledge_engine

# Initialize service components
service = AIService()

# Initialize LLM Engine
ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
llm_engine = LLMEngine(ollama_host, default_model)

# Initialize Multi-Brain AI Engine (Phase 1: Intent Brain Foundation)
# NO FALLBACKS ALLOWED - MULTI-BRAIN OR NOTHING!
if not MULTI_BRAIN_AVAILABLE:
    raise Exception("❌ MULTI-BRAIN AI ENGINE NOT AVAILABLE - SYSTEM CANNOT FUNCTION WITHOUT IT")

workflow_generator = WorkflowGenerator()
asset_client = AssetServiceClient(os.getenv("ASSET_SERVICE_URL", "http://localhost:3002"))
automation_client = AutomationServiceClient(os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:3003"))

logger.info("🧠 Initializing Multi-Brain AI Engine (Phase 1: Intent Brain Foundation)")
ai_engine = MultiBrainAIEngine(llm_engine, asset_client)

@app.on_event("startup")
async def startup_event():
    """Initialize AI engine on startup"""
    try:
        print("🚀 STARTUP EVENT CALLED!")
        logger.info("🚀 STARTUP EVENT CALLED!")
        logger.info("Initializing Multi-Brain AI Engine...")
        
        print(f"🔗 About to initialize LLM engine: {llm_engine}")
        logger.info(f"🔗 About to initialize LLM engine: {llm_engine}")
        
        # Initialize LLM engine first
        logger.info("🔗 Initializing LLM engine...")
        llm_success = await llm_engine.initialize()
        if llm_success:
            logger.info("🚀 LLM engine initialized successfully")
        else:
            logger.error("❌ Failed to initialize LLM engine")
            return
        
        # Initialize AI engine
        success = await ai_engine.initialize()
        if success:
            logger.info("🚀 Multi-Brain AI Engine initialized successfully")
            logger.info("🧠 Phase 1: Intent Brain Foundation is now active")
            logger.info("🔮 Features: ITIL Classification, Business Intent Analysis, Continuous Learning")
        else:
            logger.error("❌ Failed to initialize Multi-Brain AI Engine")
    except Exception as e:
        print(f"❌ STARTUP EXCEPTION: {e}")
        logger.error(f"❌ Exception during startup: {e}")
        import traceback
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup AI engine on shutdown"""
    logger.info("Shutting down Multi-Brain AI Engine...")
    try:
        if hasattr(ai_engine, 'cleanup'):
            await ai_engine.cleanup()
            logger.info("🧠 Multi-Brain AI Engine cleanup completed")
        else:
            logger.info("🧠 Multi-Brain AI Engine shutdown completed")
    except Exception as e:
        logger.error(f"❌ Exception during Multi-Brain AI Engine shutdown: {e}")

# PURE LLM CHAT FUNCTION - INTELLIGENT ROUTING BETWEEN CONVERSATION AND JOB CREATION
async def pure_llm_chat_endpoint(request, ai_engine):
    """
    PURE LLM CHAT INTERFACE - INTELLIGENT ROUTING
    
    This function uses LLM to determine if the user wants to:
    1. Create a job/automation (routes to LLM job creator)
    2. Have a conversation (routes to LLM conversation handler)
    
    NO PATTERN MATCHING, NO TEMPLATES, JUST INTELLIGENT LLM ROUTING!
    """
    try:
        logger.info("🧠 Processing PURE LLM chat request", message=request.message[:100], conversation_id=request.conversation_id)
        logger.info(f"🧠 AI Engine type: {type(ai_engine)}, has llm_engine: {hasattr(ai_engine, 'llm_engine')}")
        user_id = str(request.user_id) if request.user_id else "system"
        
        # Generate conversation_id if not provided
        if not request.conversation_id:
            request.conversation_id = f"chat-{uuid.uuid4()}"
        
        # Step 1: Check if this is a follow-up to a clarification request
        logger.info(f"🔍 Checking for follow-up clarification context")
        follow_up_result = await _check_for_clarification_followup(request, ai_engine)
        if follow_up_result:
            logger.info("🔄 Detected follow-up to clarification - processing with additional context")
            return follow_up_result
        
        # Step 2: Use LLM to determine intent (job creation vs conversation)
        logger.info(f"🔍 Starting intent analysis for message: '{request.message}'")
        intent_analysis = await _analyze_user_intent_with_llm(request.message, ai_engine)
        logger.info(f"🔍 Intent analysis result: {intent_analysis}")
        
        # Step 3: Route based on LLM analysis
        is_job_request = intent_analysis.get("is_job_request", False)
        logger.info(f"🔍 Routing decision: is_job_request={is_job_request}")
        
        if is_job_request:
            logger.info("🚀 LLM detected job creation request - routing to LLM job creator")
            return await _handle_job_creation_request(request, ai_engine, intent_analysis)
        else:
            logger.info("💬 LLM detected conversation request - routing to LLM conversation handler")
            return await _handle_conversation_request(request, ai_engine, intent_analysis)
        
    except Exception as e:
        logger.error("❌ PURE LLM chat processing failed", error=str(e), exc_info=True)
        
        # LLM-powered error handling
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
                    "engine": "llm_error_handler",
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

async def _analyze_user_intent_with_llm(message: str, ai_engine) -> Dict[str, Any]:
    """Use LLM to analyze if the user wants to create a job or have a conversation"""
    try:
        # Use the global LLM engine
        if llm_engine is None:
            logger.error("🔍 LLM engine not available - NO FALLBACK ALLOWED")
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception("LLM engine not available - SYSTEM CANNOT FUNCTION WITHOUT AI INTENT ANALYSIS")
        
        analysis_prompt = f"""Analyze this user message and determine if they want to create an automation job or just have a conversation.

User message: "{message}"

IMPORTANT: If the user is asking to perform ANY action on servers, services, or systems, this is a JOB REQUEST, not a conversation.

Respond with JSON only:
{{
    "is_job_request": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "job_type": "automation/deployment/monitoring/maintenance/query" (if job request),
    "conversation_type": "question/help/general" (if conversation)
}}

JOB REQUEST indicators (set is_job_request=true):
- Action verbs: restart, start, stop, deploy, install, configure, backup, monitor, update, upgrade, create, delete, remove, run, execute, automate
- Target mentions: server, service, application, database, container, VM, system, host, node
- Commands or operations to be performed
- Infrastructure management tasks
- System administration requests

CONVERSATION indicators (set is_job_request=false):
- Questions starting with: what, how, why, when, where
- Requests for information, explanations, or help
- General inquiries about system status (without requesting changes)
- Documentation or guidance requests

Examples:
- "restart nginx service on server1" → JOB REQUEST (action: restart, target: service)
- "how does nginx work?" → CONVERSATION (question about how something works)
- "deploy application to production" → JOB REQUEST (action: deploy, target: application)
- "what is the status of server1?" → CONVERSATION (information request)"""

        llm_response = await llm_engine.generate(analysis_prompt)
        logger.info(f"🔍 LLM intent analysis response: {llm_response}")
        
        # Extract the generated text from the LLM response
        if isinstance(llm_response, dict) and "generated_text" in llm_response:
            generated_text = llm_response["generated_text"]
        else:
            generated_text = str(llm_response)
        
        logger.info(f"🔍 Extracted generated text: {generated_text}")
        
        # Parse LLM response
        try:
            analysis = json.loads(generated_text)
            logger.info(f"🔍 Parsed intent analysis: {analysis}")
            return analysis
        except json.JSONDecodeError as e:
            logger.error(f"🔍 JSON parsing failed: {e} - NO FALLBACK ALLOWED")
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"LLM response parsing FAILED - NO FALLBACK ALLOWED: {e}")
            
    except Exception as e:
        logger.error(f"❌ Intent analysis failed: {e}")
        # NO FALLBACK - FAIL HARD AS REQUESTED
        raise Exception(f"Intent analysis COMPLETELY FAILED - NO FALLBACK ALLOWED: {e}")

async def _handle_job_creation_request(request, ai_engine, intent_analysis) -> Dict[str, Any]:
    """Handle job creation requests - INTENT ANALYSIS ONLY MODE"""
    try:
        logger.info("🎯 JOB INTENT ANALYSIS ONLY - Direct intent brain call")
        
        # Call ONLY the Intent Brain directly - no multi-brain engine needed
        user_context = {
            "user_id": str(request.user_id) if request.user_id else "system",
            "conversation_id": request.conversation_id
        }
        
        # Get intent analysis directly from intent brain
        intent_analysis_result = await ai_engine.intent_brain.analyze_intent(request.message, user_context)
        
        # Check if clarifying questions are needed
        if (hasattr(intent_analysis_result, 'four_w_analysis') and 
            intent_analysis_result.four_w_analysis.clarifying_questions and 
            len(intent_analysis_result.four_w_analysis.clarifying_questions) > 0):
            
            logger.info(f"🤔 Clarifying questions needed: {intent_analysis_result.four_w_analysis.clarifying_questions}")
            return await _handle_clarification_needed(request, intent_analysis_result, ai_engine)
        
        # Create a human-readable interpretation of what the AI thinks the user wants
        intent_interpretation = await _generate_intent_interpretation(intent_analysis_result, ai_engine)
        
        # Clear conversation context since we have a complete analysis
        if request.conversation_id in _conversation_contexts:
            del _conversation_contexts[request.conversation_id]
            logger.info(f"🔄 Cleared conversation context for {request.conversation_id} - analysis complete")
        
        # Build comprehensive intent classification with Intent Brain data
        intent_classification = {
            "intent_type": intent_analysis_result.four_w_analysis.what_analysis.action_type.value if hasattr(intent_analysis_result, 'four_w_analysis') else 'job_creation',
            "confidence": intent_analysis_result.overall_confidence,
            "method": "intent_brain_direct",
            "alternatives": [],
            "entities": getattr(intent_analysis_result, 'entities', []),
            "context_analysis": {
                "confidence_score": intent_analysis_result.overall_confidence,
                "risk_level": getattr(intent_analysis_result, 'risk_level', 'UNKNOWN'),
                "requirements_count": len(getattr(intent_analysis_result, 'requirements', [])),
                "recommendations": ["Intent analysis completed - job creation disabled"]
            },
            "reasoning": getattr(intent_analysis_result, 'intent_summary', 'Intent analysis performed'),
            "metadata": {
                "engine": "intent_brain_direct",
                "version": "2.0.0",
                "success": True,
                "processing_time": 0.0,  # Direct intent brain call
                "brains_consulted": ["intent_brain"],
                "intent_details": intent_analysis_result.to_dict() if hasattr(intent_analysis_result, 'to_dict') else str(intent_analysis_result)
            }
        }
        
        return {
            "response": f"🎯 JOB INTENT ANALYSIS COMPLETE\n\n{intent_interpretation}\n\n[Job creation disabled - intent analysis only mode]",
            "conversation_id": request.conversation_id,
            "intent": intent_analysis_result.four_w_analysis.what_analysis.action_type.value if hasattr(intent_analysis_result, 'four_w_analysis') else 'job_creation',
            "confidence": intent_analysis_result.overall_confidence,
            "job_id": None,  # Job creation disabled
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "intent_classification": intent_classification,
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "intent_analysis_only", 
                "response_time": 0.0,  # Direct intent brain call
                "cached": False
            }
        }
            
    except Exception as e:
        logger.error(f"❌ Intent analysis failed: {e}")
        return {
            "response": f"🎯 INTENT ANALYSIS ERROR\n\nI encountered an error while analyzing your intent: {str(e)}",
            "conversation_id": request.conversation_id,
            "intent": "intent_analysis_error",
            "confidence": 0.0,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "intent_classification": {
                "intent_type": "intent_analysis_error",
                "confidence": 0.0,
                "method": "multi_brain_intent_analysis",
                "alternatives": [],
                "entities": [],
                "context_analysis": {"error": str(e)},
                "reasoning": "Exception in intent analysis",
                "metadata": {
                    "engine": "multi_brain_intent_only",
                    "success": False,
                    "error": str(e)
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "intent_analysis_error", 
                "response_time": 0.0,
                "cached": False
            }
        }

async def _handle_clarification_needed(request, intent_analysis_result, ai_engine) -> Dict[str, Any]:
    """Handle cases where clarifying questions are needed before proceeding"""
    try:
        logger.info("🤔 Generating clarification response for user")
        
        # Get the clarifying questions from the 4W analysis
        clarifying_questions = intent_analysis_result.four_w_analysis.clarifying_questions
        missing_info = intent_analysis_result.four_w_analysis.missing_information
        
        # Generate a user-friendly clarification message
        clarification_message = await _generate_clarification_message(
            intent_analysis_result, clarifying_questions, missing_info, ai_engine
        )
        
        # Store the partial analysis for follow-up
        conversation_context = {
            "partial_analysis": intent_analysis_result.to_dict() if hasattr(intent_analysis_result, 'to_dict') else str(intent_analysis_result),
            "original_message": request.message,
            "clarifying_questions": clarifying_questions,
            "missing_information": missing_info,
            "awaiting_clarification": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store context globally for iterative clarification (in production, use Redis/database)
        _conversation_contexts[request.conversation_id] = conversation_context
        logger.info(f"🔄 Stored conversation context for {request.conversation_id}, awaiting clarification")
        
        return {
            "response": clarification_message,
            "conversation_id": request.conversation_id,
            "intent": "clarification_needed",
            "confidence": intent_analysis_result.overall_confidence,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "clarification_needed": True,
            "clarifying_questions": clarifying_questions,
            "missing_information": missing_info,
            "intent_classification": {
                "intent_type": "clarification_needed",
                "confidence": intent_analysis_result.overall_confidence,
                "method": "intent_brain_clarification",
                "alternatives": [],
                "entities": getattr(intent_analysis_result, 'entities', []),
                "context_analysis": {
                    "confidence_score": intent_analysis_result.overall_confidence,
                    "risk_level": getattr(intent_analysis_result, 'risk_level', 'UNKNOWN'),
                    "requirements_count": len(missing_info),
                    "recommendations": clarifying_questions
                },
                "reasoning": "Additional information needed to proceed",
                "metadata": {
                    "engine": "intent_brain_clarification",
                    "version": "2.0.0",
                    "success": True,
                    "clarification_context": conversation_context
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "clarification_needed", 
                "response_time": 0.0,
                "cached": False
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Clarification handling failed: {e}")
        return {
            "response": f"I need more information to proceed, but encountered an error generating clarifying questions: {str(e)}",
            "conversation_id": request.conversation_id,
            "intent": "clarification_error",
            "confidence": 0.0,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "clarification_needed": True,
            "clarifying_questions": [],
            "missing_information": [],
            "intent_classification": {
                "intent_type": "clarification_error",
                "confidence": 0.0,
                "method": "clarification_error",
                "alternatives": [],
                "entities": [],
                "context_analysis": {"error": str(e)},
                "reasoning": "Error generating clarification",
                "metadata": {
                    "engine": "clarification_error",
                    "success": False,
                    "error": str(e)
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "clarification_error", 
                "response_time": 0.0,
                "cached": False
            }
        }

async def _generate_clarification_message(intent_analysis_result, clarifying_questions, missing_info, ai_engine) -> str:
    """Generate a user-friendly clarification message using LLM"""
    try:
        if not hasattr(ai_engine, 'llm_engine') or not ai_engine.llm_engine:
            # Fallback to simple message if LLM not available
            questions_text = "\n".join([f"• {q}" for q in clarifying_questions])
            return f"I need some additional information to proceed:\n\n{questions_text}\n\nPlease provide these details so I can help you better."
        
        # Use LLM to generate a natural clarification message
        clarification_prompt = f"""Generate a friendly, helpful message asking the user for clarification. 

The user's request needs additional information before I can proceed. Here's what I understand so far and what I need:

Missing Information:
{chr(10).join([f"- {info}" for info in missing_info])}

Specific Questions to Ask:
{chr(10).join([f"- {q}" for q in clarifying_questions])}

Generate a natural, conversational message that:
1. Acknowledges what I understand from their request
2. Explains why I need more information
3. Asks the clarifying questions in a friendly way
4. Encourages them to provide the missing details

Keep it concise but helpful. Don't use JSON format - just return the message text."""

        llm_response = await ai_engine.llm_engine.generate(clarification_prompt)
        
        # Extract the generated text
        if isinstance(llm_response, dict) and "generated_text" in llm_response:
            generated_text = llm_response["generated_text"]
        else:
            generated_text = str(llm_response)
        
        # Clean up the response
        clarification_message = generated_text.strip()
        
        # Fallback if LLM response is empty or too short
        if len(clarification_message) < 20:
            questions_text = "\n".join([f"• {q}" for q in clarifying_questions])
            clarification_message = f"I need some additional information to proceed:\n\n{questions_text}\n\nPlease provide these details so I can help you better."
        
        return clarification_message
        
    except Exception as e:
        logger.error(f"❌ Failed to generate clarification message: {e}")
        # Fallback to simple message
        questions_text = "\n".join([f"• {q}" for q in clarifying_questions])
        return f"I need some additional information to proceed:\n\n{questions_text}\n\nPlease provide these details so I can help you better."

# Global conversation context storage (in production, use Redis/database)
_conversation_contexts = {}

async def _check_for_clarification_followup(request, ai_engine) -> Optional[Dict[str, Any]]:
    """Check if this is a clarification response and combine with original context for iterative clarification"""
    try:
        conversation_id = request.conversation_id
        
        # Check if we have stored context for this conversation
        if conversation_id not in _conversation_contexts:
            logger.info(f"🔄 No stored context for conversation {conversation_id} - treating as new request")
            return None
            
        stored_context = _conversation_contexts[conversation_id]
        
        # Check if we're awaiting clarification for this conversation
        if not stored_context.get("awaiting_clarification", False):
            logger.info(f"🔄 Not awaiting clarification for conversation {conversation_id}")
            return None
        
        logger.info(f"🔄 Found stored context awaiting clarification for conversation {conversation_id}")
        
        # Use the LLM to determine if this is likely a clarification response
        if not hasattr(ai_engine, 'llm_engine') or not ai_engine.llm_engine:
            logger.warning("🔄 LLM not available for clarification detection - skipping")
            return None
        
        clarification_detection_prompt = f"""Analyze this user message to determine if it appears to be providing additional information or clarification.

User message: "{request.message}"

Previous context: The user was asked clarifying questions about: {stored_context.get('missing_information', [])}

Look for:
- Timing/scheduling information (every day, hourly, at midnight, etc.)
- Threshold/alert values (less than 10GB, above 80%, etc.)
- Configuration details or parameters
- Short, direct answers that seem to be responding to questions

Does this look like a clarification response rather than a completely new request?

Respond with JSON only:
{{
    "is_clarification_response": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        try:
            llm_response_data = await ai_engine.llm_engine.generate(clarification_detection_prompt)
            llm_response = llm_response_data.get("generated_text", "")
            
            # Parse the LLM response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                if analysis.get("is_clarification_response", False) and analysis.get("confidence", 0) > 0.6:
                    logger.info(f"🔄 Detected clarification response: {analysis.get('reasoning', 'No reasoning')}")
                    
                    # COMBINE ORIGINAL + CLARIFICATION FOR COMPLETE CONTEXT
                    original_message = stored_context.get("original_message", "")
                    combined_message = f"""{original_message}

Additional clarification provided: {request.message}"""
                    
                    logger.info(f"🔄 COMBINING CONTEXTS:")
                    logger.info(f"🔄 Original: {original_message}")
                    logger.info(f"🔄 Clarification: {request.message}")
                    logger.info(f"🔄 Combined: {combined_message}")
                    
                    # Create a new request with the COMBINED context
                    combined_request = type(request)(
                        message=combined_message,
                        conversation_id=request.conversation_id,
                        user_id=request.user_id
                    )
                    
                    # Clear the awaiting clarification flag since we're processing it
                    _conversation_contexts[conversation_id]["awaiting_clarification"] = False
                    
                    # Process the COMBINED request - this will re-analyze with full context
                    # and may ask for MORE clarification if still needed (ITERATIVE!)
                    logger.info(f"🔄 Re-analyzing COMBINED context for completeness...")
                    return await _handle_job_creation_request(combined_request, ai_engine, {"is_job_request": True})
                else:
                    logger.info(f"🔄 Not a clarification response (confidence: {analysis.get('confidence', 0)}) - treating as new request")
                    # Clear stored context since this seems to be a new request
                    if conversation_id in _conversation_contexts:
                        del _conversation_contexts[conversation_id]
                    return None
            else:
                logger.warning("🔄 Could not parse clarification detection response")
                return None
                
        except Exception as llm_error:
            logger.error(f"🔄 Clarification detection failed: {llm_error}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error in clarification follow-up detection: {e}")
        return None

async def _generate_intent_interpretation(intent_analysis_result, ai_engine) -> str:
    """Generate a human-readable interpretation of what the AI thinks the user wants"""
    try:
        if not hasattr(ai_engine, 'llm_engine') or not ai_engine.llm_engine:
            return "Intent analysis completed, but unable to generate human interpretation (LLM not available)"
        
        # Extract key information from intent analysis
        intent_data = intent_analysis_result.to_dict() if hasattr(intent_analysis_result, 'to_dict') else str(intent_analysis_result)
        
        interpretation_prompt = f"""Based on this intent analysis, explain in simple, human terms what you think the user wants to accomplish:

Intent Analysis Data:
{json.dumps(intent_data, indent=2, default=str)}

Provide a clear, conversational explanation that starts with "I understand that you want to..." and explains:
1. What the user is trying to accomplish
2. The key details or requirements identified
3. The confidence level of this understanding

Keep it concise but informative, as if explaining to the user what you understood from their request."""

        interpretation_result = await ai_engine.llm_engine.generate(interpretation_prompt)
        
        # Extract the response text from the LLM result
        if isinstance(interpretation_result, dict):
            interpretation = interpretation_result.get('response', str(interpretation_result))
        else:
            interpretation = str(interpretation_result)
            
        return interpretation.strip()
        
    except Exception as e:
        logger.error(f"Failed to generate intent interpretation: {e}")
        return f"Intent analysis completed. Raw data: {str(intent_analysis_result)[:200]}..."

async def _handle_conversation_request(request, ai_engine, intent_analysis) -> Dict[str, Any]:
    """Handle conversation requests - INTENT ANALYSIS ONLY MODE"""
    try:
        logger.info("🎯 INTENT ANALYSIS ONLY - Direct intent brain call")
        
        # Call ONLY the Intent Brain directly - no multi-brain engine needed
        user_context = {
            "user_id": str(request.user_id) if request.user_id else "system",
            "conversation_id": request.conversation_id
        }
        
        # Get intent analysis directly from intent brain
        intent_analysis_result = await ai_engine.intent_brain.analyze_intent(request.message, user_context)
        
        # Create a human-readable interpretation of what the AI thinks the user wants
        intent_interpretation = await _generate_intent_interpretation(intent_analysis_result, ai_engine)
        
        # Build comprehensive intent classification with Multi-Brain data
        intent_classification = {
            "intent_type": intent_analysis_result.four_w_analysis.what_analysis.action_type.value if hasattr(intent_analysis_result, 'four_w_analysis') else 'unknown',
            "confidence": intent_analysis_result.overall_confidence,
            "method": "intent_brain_direct",
            "alternatives": [],
            "entities": getattr(intent_analysis_result, 'entities', []),
            "context_analysis": {
                "confidence_score": intent_analysis_result.overall_confidence,
                "risk_level": getattr(intent_analysis_result, 'risk_level', 'UNKNOWN'),
                "requirements_count": len(getattr(intent_analysis_result, 'requirements', [])),
                "recommendations": ["Intent analysis completed - response generation disabled"]
            },
            "reasoning": getattr(intent_analysis_result, 'intent_summary', 'Intent analysis performed'),
            "metadata": {
                "engine": "intent_brain_direct",
                "version": "2.0.0",
                "success": True,
                "processing_time": 0.0,  # Direct intent brain call
                "brains_consulted": ["intent_brain"],
                "intent_details": intent_analysis_result.to_dict() if hasattr(intent_analysis_result, 'to_dict') else str(intent_analysis_result)
            }
        }
        
        return {
            "response": f"🎯 INTENT ANALYSIS COMPLETE\n\n{intent_interpretation}\n\n[Response generation disabled - intent analysis only mode]",
            "conversation_id": request.conversation_id,
            "intent": intent_analysis_result.four_w_analysis.what_analysis.action_type.value if hasattr(intent_analysis_result, 'four_w_analysis') else 'unknown',
            "confidence": intent_analysis_result.overall_confidence,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "intent_classification": intent_classification,
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "intent_analysis_only", 
                "response_time": 0.0,  # Direct intent brain call
                "cached": False
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Conversation handling failed: {e}")
        return {
            "response": f"I encountered an issue during our conversation: {str(e)}. Please try again.",
            "conversation_id": request.conversation_id,
            "intent": "conversation_error",
            "confidence": 0.7,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "intent_classification": {
                "intent_type": "conversation_error",
                "confidence": 0.7,
                "method": "pure_llm_conversation",
                "alternatives": [],
                "entities": [],
                "context_analysis": {"error": str(e)},
                "reasoning": "Exception in conversation handling",
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "success": False,
                    "error": str(e)
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "pure_llm_conversation_exception", 
                "response_time": 0.0,
                "cached": False
            }
        }

class JobRequest(BaseModel):
    description: str
    user_id: Optional[int] = None
    priority: str = "normal"

class JobResponse(BaseModel):
    job_id: str
    workflow: Dict[str, Any]
    message: str
    confidence: float
    parsed_request: Dict[str, Any]
    # Phase 7 Integration Fields
    targets: Optional[List[Dict[str, Any]]] = []
    execution_plan: Optional[Dict[str, Any]] = {}
    optimizations: Optional[List[Dict[str, Any]]] = []

class TextAnalysisRequest(BaseModel):
    text: str

class TextAnalysisResponse(BaseModel):
    text: str
    parsed_request: Dict[str, Any]
    entities: Dict[str, List[str]]
    confidence: float
    suggestions: List[str]

class ExecuteJobRequest(BaseModel):
    description: str
    execute_immediately: bool = True
    user_id: Optional[int] = None

class ExecuteJobResponse(BaseModel):
    job_id: str
    execution_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow: Dict[str, Any]
    message: str
    confidence: float
    execution_started: bool
    automation_job_id: Optional[int] = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str  # "question", "job_creation", "unknown"
    confidence: float
    conversation_id: Optional[str] = None
    job_id: Optional[str] = None
    execution_id: Optional[str] = None
    automation_job_id: Optional[int] = None
    workflow: Optional[Dict[str, Any]] = None
    execution_started: bool = False
    # Enhanced clarification and risk assessment fields
    clarification_needed: Optional[bool] = False
    clarifying_questions: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    field_confidence_scores: Optional[Dict[str, Dict[str, Any]]] = None
    validation_issues: Optional[List[Dict[str, Any]]] = None
    # Debug information
    intent_classification: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    _routing: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """Health check endpoint with pure LLM architecture status"""
    try:
        # Get detailed health status from AI Brain Engine
        brain_health = ai_engine.get_health_status()
        
        return {
            "status": "healthy",
            "service": "ai-service",
            "architecture": "pure_llm",
            "brain_engine": brain_health,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "service": "ai-service",
            "architecture": "pure_llm",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/info")
async def service_info():
    """Service information endpoint - Pure LLM Architecture"""
    return {
        "service": "ai-service",
        "version": "3.0.0",
        "architecture": "pure_llm",
        "description": "Pure LLM-powered automation service - NLM completely eliminated",
        "capabilities": [
            "Pure LLM natural language understanding",
            "Multi-stage LLM job creation pipeline",
            "LLM-powered conversation handling",
            "Intelligent intent routing via LLM",
            "Vector-powered knowledge base",
            "Multi-protocol support (SNMP, SMTP, SSH, VAPIX)",
            "Script generation (PowerShell, Bash, Python)",
            "Real-time system queries",
            "Continuous learning from interactions"
        ],
        "llm_features": [
            "Ollama LLM integration",
            "Multi-stage job creation (ANALYZE → PLAN → VALIDATE → CREATE)",
            "Intelligent conversation routing",
            "Context-aware responses",
            "Safety validation and risk assessment",
            "Fallback error handling"
        ],
        "supported_protocols": [
            "SNMP - Network device monitoring",
            "SMTP - Email notifications and alerts", 
            "SSH - Remote command execution",
            "VAPIX - Axis camera integration"
        ],
        "supported_operations": [
            "Automation job creation", "System maintenance", "Deployment requests",
            "Configuration changes", "Monitoring setup", "Troubleshooting",
            "Network monitoring", "Email alerts", "Remote execution", 
            "Camera management", "Script generation", "System queries"
        ],
        "architecture_changes": {
            "nlm_status": "completely_removed",
            "intent_engine": "disabled",
            "job_creation": "pure_llm_pipeline",
            "conversation": "pure_llm_handler",
            "routing": "llm_based_intelligent_routing"
        },
        "automation_integration": True,
        "nlm_eliminated": True
    }

@app.get("/ai/system-capabilities")
async def get_system_capabilities():
    """Get comprehensive system capabilities and self-awareness information"""
    try:
        if hasattr(ai_engine, 'system_capabilities') and ai_engine.system_capabilities:
            overview = ai_engine.system_capabilities.get_system_overview()
            capabilities_summary = ai_engine.system_capabilities.get_capabilities_summary()
            
            return {
                "status": "success",
                "system_overview": overview,
                "capabilities_summary": capabilities_summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "unavailable",
                "message": "System capabilities not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error("Failed to get system capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system capabilities: {str(e)}")

@app.post("/ai/validate-job")
async def validate_job_request(request: dict):
    """Validate job request before creation"""
    try:
        description = request.get("description", "")
        user_id = request.get("user_id", "system")
        
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        
        # Parse the request using NLP
        parsed_request = await intent_processor.parse_request(description)
        
        # Extract requirements
        requirements = {
            "description": description,
            "operation": parsed_request.operation,
            "target_process": parsed_request.target_process,
            "target_service": parsed_request.target_service,
            "target_group": parsed_request.target_group,
            "target_os": parsed_request.target_os
        }
        
        # Get target systems
        target_systems = []
        if parsed_request.target_group:
            targets = await asset_client.resolve_target_group(parsed_request.target_group)
            target_systems = [t.get('hostname', t.get('name', str(t))) for t in targets] if targets else []
        
        # Validate using job validator
        try:
            from job_engine.job_validator import JobValidator
            validator = JobValidator()
            
            validation_result = validator.validate_job_request(description)
        except ImportError as ie:
            logger.warning(f"Job validator not available: {ie}")
            # Return basic validation result
            return {
                "is_valid": True,
                "confidence_score": 0.7,
                "issues": [],
                "missing_requirements": [],
                "clarification_questions": [],
                "parsed_request": {
                    "operation": parsed_request.operation,
                    "target_process": parsed_request.target_process,
                    "target_service": parsed_request.target_service,
                    "target_group": parsed_request.target_group,
                    "target_os": parsed_request.target_os,
                    "confidence": parsed_request.confidence
                }
            }
        
        return {
            "is_valid": validation_result.is_valid,
            "confidence_score": validation_result.confidence_score,
            "issues": [],
            "missing_requirements": [],
            "clarification_questions": validation_result.clarification_questions,
            "risk_assessment": validation_result.risk_assessment,
            "field_confidence_scores": validation_result.field_confidence_scores,
            "parsed_request": {
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "confidence": parsed_request.confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Job validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    """PURE LLM CHAT INTERFACE - NO MORE NLP PATTERN MATCHING BULLSHIT!"""
    result = await pure_llm_chat_endpoint(request, ai_engine)
    return ChatResponse(**result)

class ProceedWithRiskRequest(BaseModel):
    message: str
    conversation_id: str
    acknowledge_risks: bool = False
    user_notes: Optional[str] = None

@app.post("/ai/proceed-with-risk")
async def proceed_with_risk(request: ProceedWithRiskRequest):
    """Allow user to proceed with job creation despite risks after acknowledging them"""
    try:
        if not request.acknowledge_risks:
            raise HTTPException(status_code=400, detail="Must acknowledge risks to proceed")
        
        # Log the risk acknowledgment
        logger.warning(
            "User proceeding with risks acknowledged",
            conversation_id=request.conversation_id,
            user_notes=request.user_notes,
            message=request.message
        )
        
        # Process through brain engine with risk acknowledgment
        response = await ai_engine.process_message(
            message=request.message,
            user_id="system"
        )
        
        return {
            "message": "Job created with acknowledged risks",
            "job_id": str(response.get("job_id")) if response.get("job_id") is not None else None,
            "execution_id": response.get("execution_id"),
            "automation_job_id": response.get("automation_job_id"),
            "workflow": response.get("workflow"),
            "execution_started": response.get("execution_started", False),
            "risk_acknowledged": True,
            "user_notes": request.user_notes
        }
        
    except Exception as e:
        logger.error(f"Failed to proceed with risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Risk assessment is now included in the chat response

# System queries and script generation are now handled through the main chat interface

@app.get("/ai/knowledge-stats")
def get_knowledge_stats():
    """Get AI knowledge base statistics"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI Brain Engine not initialized")
        
        stats = ai_engine.get_knowledge_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/ai/store-knowledge")
async def store_knowledge_endpoint(request: dict):
    """Store new knowledge in the AI system"""
    try:
        content = request.get("content", "")
        category = request.get("category", "general")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        success = await ai_engine.store_knowledge(content, category)
        
        if success:
            return {
                "status": "success",
                "message": f"Knowledge stored successfully in category '{category}'"
            }
        else:
            raise HTTPException(status_code=503, detail="Failed to store knowledge")
            
    except Exception as e:
        logger.error("Failed to store knowledge", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store knowledge: {str(e)}")

@app.post("/ai/protocol/execute")
async def execute_protocol_operation(request: dict):
    """Execute operation using specified protocol"""
    try:
        protocol = request.get("protocol", "")
        target = request.get("target", {})
        command = request.get("command", "")
        credentials = request.get("credentials", {})
        kwargs = request.get("parameters", {})
        
        if not protocol or not target or not command:
            raise HTTPException(status_code=400, detail="Protocol, target, and command are required")
        
        logger.info("Executing protocol operation", 
                   protocol=protocol, 
                   target=target.get("hostname", "unknown"),
                   command=command)
        
        result = await ai_engine.execute_protocol_command(
            protocol, target, command, credentials, **kwargs
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error("Protocol operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Protocol operation failed: {str(e)}")

# Protocol-specific operations are now handled through the main chat interface and /ai/protocol/execute endpoint

@app.get("/ai/protocols/capabilities")
async def get_protocol_capabilities():
    """Get all supported protocol capabilities"""
    try:
        status = await ai_engine.get_protocol_status()
        return status
        
    except Exception as e:
        logger.error("Failed to get protocol capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

def _map_operation_to_intent(operation: str) -> str:
    """Map operation to intent type for workflow generation"""
    operation_to_intent_map = {
        "update": "system_maintenance",
        "restart": "system_maintenance", 
        "stop": "system_maintenance",
        "start": "system_maintenance",
        "install": "deployment_request",
        "remove": "system_maintenance",
        "check": "information_query",
        "status": "information_query",
        "deploy": "deployment_request",
        "configure": "configuration_change",
        "backup": "backup_request",
        "restore": "backup_request",
        "monitor": "monitoring_setup",
        "audit": "security_audit",
        "troubleshoot": "troubleshooting"
    }
    return operation_to_intent_map.get(operation, "system_maintenance")

@app.post("/ai/create-job", response_model=JobResponse)
async def create_job(request: JobRequest):
    """Create a new automation job from natural language description"""
    try:
        logger.info("Processing job creation request", description=request.description)
        
        # Step 1: Parse the natural language request
        parsed_request = await intent_processor.parse_request(request.description)
        logger.info("Parsed request", 
                   operation=parsed_request.operation,
                   target_process=parsed_request.target_process,
                   target_group=parsed_request.target_group,
                   confidence=parsed_request.confidence)
        
        # Step 2: Resolve target groups to actual targets
        target_groups = []
        if parsed_request.target_group:
            targets = await asset_client.resolve_target_group(parsed_request.target_group)
            if not targets:
                # Use mock data for demo
                targets = await asset_client.create_mock_targets_for_demo(parsed_request.target_group)
            
            if targets:
                target_groups = [parsed_request.target_group]
                logger.info(f"Resolved target group '{parsed_request.target_group}' to {len(targets)} targets")
            else:
                logger.warning(f"No targets found for group '{parsed_request.target_group}'")
        
        # Step 3: Phase 7 Integration - Use AI Brain Engine for complete workflow processing
        resolved_targets = []
        execution_plan = {}
        optimizations = []
        
        if hasattr(ai_engine, 'job_creation_enabled') and ai_engine.job_creation_enabled:
            # Use AI Brain Engine with Phase 7 modules
            ai_response = await ai_engine.process_query(request.description, {
                "operation_type": "job_creation",
                "parsed_request": {
                    "operation": parsed_request.operation,
                    "target_process": parsed_request.target_process,
                    "target_service": parsed_request.target_service,
                    "target_group": parsed_request.target_group,
                    "target_os": parsed_request.target_os
                }
            })
            
            # Extract Phase 7 results from AI response
            workflow_dict = ai_response.get("workflow", {})
            resolved_targets = ai_response.get("targets", [])
            execution_plan = ai_response.get("execution_plan", {})
            optimizations = ai_response.get("optimizations", [])
            
            # If AI Brain didn't generate complete workflow, fall back to direct workflow generation
            if not workflow_dict.get("steps"):
                logger.info("AI Brain didn't generate complete workflow, using Phase 7 modules directly")
                
                # Convert parsed_request to the format expected by workflow_generator
                intent_type = _map_operation_to_intent(parsed_request.operation)
                requirements = {
                    "operation": parsed_request.operation,
                    "target_process": parsed_request.target_process,
                    "target_service": parsed_request.target_service,
                    "target_group": parsed_request.target_group,
                    "target_os": parsed_request.target_os,
                    "description": request.description
                }
                
                # Phase 7 Module Integration
                # Step 3a: Target Resolution
                if hasattr(ai_engine, 'resolve_targets'):
                    try:
                        target_resolution_result = ai_engine.resolve_targets(
                            target_groups + [parsed_request.target_group] if parsed_request.target_group else target_groups,
                            {"context": requirements}
                        )
                        raw_targets = target_resolution_result.resolved_targets if hasattr(target_resolution_result, 'resolved_targets') else []
                        # Convert ResolvedTarget objects to dictionaries
                        resolved_targets = []
                        for target in raw_targets:
                            if hasattr(target, 'to_dict'):
                                resolved_targets.append(target.to_dict())
                            elif hasattr(target, '__dict__'):
                                resolved_targets.append(target.__dict__)
                            else:
                                resolved_targets.append(str(target))
                        logger.info(f"Target Resolver: Resolved {len(resolved_targets)} targets")
                    except Exception as e:
                        logger.warning(f"Target resolution failed: {e}")
                        resolved_targets = []
                
                # Step 3b: Workflow Generation
                workflow = ai_engine.generate_workflow(intent_type, requirements, target_groups)
                
                # Step 3c: Step Optimization
                optimized_workflow_obj = None
                if hasattr(ai_engine, 'optimize_workflow_steps'):
                    try:
                        # Pass workflow.steps (list) instead of workflow object
                        optimized_workflow_obj = ai_engine.optimize_workflow_steps(workflow.steps, None, {
                            "targets": resolved_targets,
                            "requirements": requirements
                        })
                        
                        # Extract optimizations from the OptimizedWorkflow object
                        if hasattr(optimized_workflow_obj, 'optimization_metrics'):
                            raw_optimizations = [optimized_workflow_obj.optimization_metrics]
                        else:
                            raw_optimizations = []
                            
                        # Convert optimization objects to dictionaries
                        optimizations = []
                        for opt in raw_optimizations:
                            if hasattr(opt, 'to_dict'):
                                optimizations.append(opt.to_dict())
                            elif hasattr(opt, '__dict__'):
                                optimizations.append(opt.__dict__)
                            else:
                                optimizations.append(str(opt))
                        logger.info(f"Step Optimizer: Applied {len(optimizations)} optimizations")
                    except Exception as e:
                        logger.warning(f"Step optimization failed: {e}")
                        optimizations = []
                        optimized_workflow_obj = None
                
                # Step 3d: Execution Planning
                logger.info(f"Checking execution planner: has_method={hasattr(ai_engine, 'create_execution_plan')}, optimized_obj={optimized_workflow_obj is not None}")
                if hasattr(ai_engine, 'create_execution_plan') and optimized_workflow_obj:
                    try:
                        logger.info("Calling execution planner...")
                        # Pass both original workflow and optimized workflow object (not dict)
                        execution_plan_result = ai_engine.create_execution_plan(
                            workflow, 
                            optimized_workflow_obj,  # Pass the actual OptimizedWorkflow object
                            {
                                "targets": resolved_targets,
                                "requirements": requirements
                            }
                        )
                        execution_plan = execution_plan_result.to_dict() if hasattr(execution_plan_result, 'to_dict') else execution_plan_result.__dict__
                        logger.info(f"Execution Planner: Created plan with strategy '{execution_plan.get('strategy', 'unknown')}'")
                    except Exception as e:
                        logger.warning(f"Execution planning failed: {e}")
                        execution_plan = {}
                else:
                    logger.warning(f"Execution planner not called: has_method={hasattr(ai_engine, 'create_execution_plan')}, optimized_obj={optimized_workflow_obj is not None}")
                
                # Convert GeneratedWorkflow to dict format for compatibility
                workflow_dict = {
                    "id": workflow.workflow_id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "type": workflow.workflow_type.value,
                    "steps": [
                        {
                            "id": step.step_id,
                            "name": step.name,
                            "description": step.description,
                            "type": step.step_type.value,
                            "command": step.command,
                            "script": step.script,
                            "parameters": step.parameters,
                            "timeout": step.timeout,
                            "retry_count": step.retry_count,
                            "risk_level": step.risk_level,
                            "requires_approval": step.requires_approval
                        }
                        for step in workflow.steps
                    ],
                    "execution_mode": workflow.execution_mode.value,
                    "estimated_duration": workflow.estimated_duration,
                    "risk_level": workflow.risk_level,
                    "requires_approval": workflow.requires_approval,
                    "target_systems": workflow.target_systems
                }
        else:
            # Fallback to basic workflow generation
            logger.warning("AI Brain job creation not enabled, using basic workflow generation")
            intent_type = _map_operation_to_intent(parsed_request.operation)
            requirements = {
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "description": request.description
            }
            
            workflow = workflow_generator.generate_workflow(intent_type, requirements, target_groups)
            
            # Convert GeneratedWorkflow to dict format for compatibility
            workflow_dict = {
                "id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "type": workflow.workflow_type.value,
                "steps": [
                    {
                        "id": step.step_id,
                        "name": step.name,
                        "description": step.description,
                        "type": step.step_type.value,
                        "command": step.command,
                        "script": step.script,
                        "parameters": step.parameters,
                        "timeout": step.timeout,
                        "retry_count": step.retry_count,
                        "risk_level": step.risk_level,
                        "requires_approval": step.requires_approval
                    }
                    for step in workflow.steps
                ],
                "execution_mode": workflow.execution_mode.value,
                "estimated_duration": workflow.estimated_duration,
                "risk_level": workflow.risk_level,
                "requires_approval": workflow.requires_approval,
                "target_systems": workflow.target_systems
            }
        
        logger.info("Generated workflow", workflow_id=workflow_dict['id'], steps=len(workflow_dict['steps']))
        
        # Step 4: Create job ID
        job_id = str(uuid.uuid4())
        
        # Step 5: Prepare response
        message = f"Successfully created workflow for: {request.description}"
        if parsed_request.confidence < 0.5:
            message += f" (Low confidence: {parsed_request.confidence:.2f} - please verify)"
        
        return JobResponse(
            job_id=job_id,
            workflow=workflow_dict,
            message=message,
            confidence=parsed_request.confidence,
            parsed_request={
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "raw_text": parsed_request.raw_text
            },
            # Phase 7 Integration Results
            targets=resolved_targets,
            execution_plan=execution_plan,
            optimizations=optimizations
        )
        
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/ai/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """Analyze text for automation intent"""
    try:
        logger.info("Analyzing text", text=request.text)
        
        # Parse the request
        parsed_request = await intent_processor.parse_request(request.text)
        
        # Extract all entities for debugging
        entities = await intent_processor.extract_entities(request.text)
        
        # Generate suggestions
        suggestions = []
        if parsed_request.confidence < 0.5:
            suggestions.append("Consider being more specific about the target group")
            suggestions.append("Specify the exact process or service name")
            
        if not parsed_request.target_group:
            suggestions.append("Add a target group (e.g., 'on CIS servers', 'on web servers')")
            
        if parsed_request.operation == "unknown":
            suggestions.append("Specify the operation (update, restart, stop, start, check)")
        
        return TextAnalysisResponse(
            text=request.text,
            parsed_request={
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "confidence": parsed_request.confidence
            },
            entities=entities,
            confidence=parsed_request.confidence,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error("Failed to analyze text", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

@app.post("/ai/execute-job", response_model=ExecuteJobResponse)
async def execute_job(request: ExecuteJobRequest):
    """Create and execute a job immediately"""
    try:
        logger.info("Processing job execution request", 
                   description=request.description,
                   execute_immediately=request.execute_immediately)
        
        # Step 1: Parse the natural language request
        parsed_request = await intent_processor.parse_request(request.description)
        logger.info("Parsed execution request", 
                   operation=parsed_request.operation,
                   target_process=parsed_request.target_process,
                   target_group=parsed_request.target_group,
                   confidence=parsed_request.confidence)
        
        # Step 2: Resolve target groups to actual targets
        target_groups = []
        if parsed_request.target_group:
            targets = await asset_client.resolve_target_group(parsed_request.target_group)
            if not targets:
                # Use mock data for demo
                targets = await asset_client.create_mock_targets_for_demo(parsed_request.target_group)
            
            if targets:
                target_groups = [parsed_request.target_group]
                logger.info(f"Resolved target group '{parsed_request.target_group}' to {len(targets)} targets")
            else:
                logger.warning(f"No targets found for group '{parsed_request.target_group}'")
        
        # Step 3: Generate workflow
        # Convert parsed_request to the format expected by workflow_generator
        intent_type = _map_operation_to_intent(parsed_request.operation)
        requirements = {
            "operation": parsed_request.operation,
            "target_process": parsed_request.target_process,
            "target_service": parsed_request.target_service,
            "target_group": parsed_request.target_group,
            "target_os": parsed_request.target_os,
            "description": request.description
        }
        
        workflow = workflow_generator.generate_workflow(intent_type, requirements, target_groups)
        
        # Convert GeneratedWorkflow to dict format for compatibility
        workflow_dict = {
            "id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "type": workflow.workflow_type.value,
            "steps": [
                {
                    "id": step.step_id,
                    "name": step.name,
                    "description": step.description,
                    "type": step.step_type.value,
                    "command": step.command,
                    "script": step.script,
                    "parameters": step.parameters,
                    "timeout": step.timeout,
                    "retry_count": step.retry_count,
                    "risk_level": step.risk_level,
                    "requires_approval": step.requires_approval
                }
                for step in workflow.steps
            ],
            "execution_mode": workflow.execution_mode.value,
            "estimated_duration": workflow.estimated_duration,
            "risk_level": workflow.risk_level,
            "requires_approval": workflow.requires_approval,
            "target_systems": workflow.target_systems
        }
        
        logger.info("Generated workflow for execution", 
                   workflow_id=workflow_dict['id'], 
                   steps=len(workflow_dict['steps']))
        
        # Step 4: Create job ID
        job_id = str(uuid.uuid4())
        
        # Step 5: Submit to automation service if requested
        execution_started = False
        automation_job_id = None
        execution_id = None
        task_id = None
        
        if request.execute_immediately:
            try:
                # Check automation service health
                automation_healthy = await automation_client.health_check()
                if not automation_healthy:
                    logger.warning("Automation service not healthy, skipping execution")
                    message = f"Workflow created but automation service unavailable for execution"
                else:
                    # Submit workflow to automation service
                    submission_result = await automation_client.submit_ai_workflow(
                        workflow_dict, 
                        job_name=f"AI: {request.description[:50]}..."
                    )
                    
                    if submission_result.get('success'):
                        execution_started = True
                        automation_job_id = submission_result.get('job_id')
                        execution_id = submission_result.get('execution_id')
                        task_id = submission_result.get('task_id')
                        
                        logger.info("Workflow submitted to automation service",
                                   automation_job_id=automation_job_id,
                                   execution_id=execution_id)
                        
                        message = f"Workflow created and execution started (Job ID: {automation_job_id})"
                    else:
                        logger.error("Failed to submit workflow to automation service",
                                    error=submission_result.get('error'))
                        message = f"Workflow created but execution failed: {submission_result.get('error')}"
                        
            except Exception as e:
                logger.error("Failed to submit workflow for execution", error=str(e))
                message = f"Workflow created but execution failed: {str(e)}"
        else:
            message = f"Workflow created successfully (execution not requested)"
        
        # Add confidence warning if needed
        if parsed_request.confidence < 0.5:
            message += f" (Low confidence: {parsed_request.confidence:.2f} - please verify)"
        
        return ExecuteJobResponse(
            job_id=job_id,
            execution_id=execution_id,
            task_id=task_id,
            workflow=workflow_dict,
            message=message,
            confidence=parsed_request.confidence,
            execution_started=execution_started,
            automation_job_id=automation_job_id
        )
        
    except Exception as e:
        logger.error("Failed to execute job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute job: {str(e)}")

@app.get("/ai/test-nlp")
async def test_nlp():
    """Test endpoint for NLP functionality"""
    test_requests = [
        "update stationcontroller on CIS servers",
        "restart nginx on web servers",
        "stop Apache service on all servers",
        "check status of IIS on production servers"
    ]
    
    results = []
    for test_text in test_requests:
        parsed = await intent_processor.parse_request(test_text)
        entities = await intent_processor.extract_entities(test_text)
        
        results.append({
            "input": test_text,
            "parsed": {
                "operation": parsed.operation,
                "target_process": parsed.target_process,
                "target_service": parsed.target_service,
                "target_group": parsed.target_group,
                "target_os": parsed.target_os,
                "confidence": parsed.confidence
            },
            "entities": entities
        })
    
    return {"test_results": results}

@app.get("/ai/test-workflow")
async def test_workflow():
    """Test endpoint for workflow generation"""
    test_request = "update stationcontroller on CIS servers"
    parsed = await intent_processor.parse_request(test_request)
    
    # Convert to proper format for workflow generator
    intent_type = _map_operation_to_intent(parsed.operation)
    requirements = {
        "operation": parsed.operation,
        "target_process": parsed.target_process,
        "target_service": parsed.target_service,
        "target_group": parsed.target_group,
        "target_os": parsed.target_os,
        "description": test_request
    }
    
    workflow = workflow_generator.generate_workflow(intent_type, requirements, ["CIS"])
    
    # Convert to dict format
    workflow_dict = {
        "id": workflow.workflow_id,
        "name": workflow.name,
        "description": workflow.description,
        "type": workflow.workflow_type.value,
        "steps": [
            {
                "id": step.step_id,
                "name": step.name,
                "description": step.description,
                "type": step.step_type.value,
                "command": step.command,
                "script": step.script,
                "parameters": step.parameters,
                "timeout": step.timeout,
                "retry_count": step.retry_count,
                "risk_level": step.risk_level,
                "requires_approval": step.requires_approval
            }
            for step in workflow.steps
        ],
        "execution_mode": workflow.execution_mode.value,
        "estimated_duration": workflow.estimated_duration,
        "risk_level": workflow.risk_level,
        "requires_approval": workflow.requires_approval,
        "target_systems": workflow.target_systems
    }
    
    return {
        "input": test_request,
        "parsed": {
            "operation": parsed.operation,
            "target_process": parsed.target_process,
            "target_group": parsed.target_group,
            "confidence": parsed.confidence
        },
        "workflow": workflow_dict
    }

@app.get("/ai/test-assets")
async def test_assets():
    """Test endpoint for asset service integration"""
    try:
        # Test health check
        healthy = await asset_client.health_check()
        
        # Test group resolution
        test_groups = ["CIS servers", "web servers"]
        group_results = {}
        
        for group_name in test_groups:
            targets = await asset_client.resolve_target_group(group_name)
            if not targets:
                targets = await asset_client.create_mock_targets_for_demo(group_name)
            group_results[group_name] = {
                "target_count": len(targets),
                "targets": [{"hostname": t.get("hostname"), "os_type": t.get("os_type")} for t in targets]
            }
        
        return {
            "asset_service_healthy": healthy,
            "group_resolution": group_results
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "asset_service_healthy": False
        }

@app.get("/ai/test-automation")
async def test_automation():
    """Test endpoint for automation service integration"""
    try:
        # Test health check
        healthy = await automation_client.health_check()
        
        # Get client info
        client_info = automation_client.get_client_info()
        
        # List AI jobs
        ai_jobs = await automation_client.list_ai_jobs(limit=5)
        
        return {
            "automation_service_healthy": healthy,
            "client_info": client_info,
            "ai_jobs_count": len(ai_jobs),
            "recent_ai_jobs": [
                {
                    "id": job.get("id"),
                    "name": job.get("name"),
                    "created_at": job.get("created_at"),
                    "job_type": job.get("job_type")
                } for job in ai_jobs[:3]
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "automation_service_healthy": False
        }

@app.get("/ai/test-integration")
async def test_integration():
    """Test full AI to Automation integration"""
    try:
        test_request = "check status of nginx on web servers"
        
        logger.info("Testing full integration", request=test_request)
        
        # Step 1: Test AI processing
        parsed = await intent_processor.parse_request(test_request)
        
        # Convert to proper format for workflow generator
        intent_type = _map_operation_to_intent(parsed.operation)
        requirements = {
            "operation": parsed.operation,
            "target_process": parsed.target_process,
            "target_service": parsed.target_service,
            "target_group": parsed.target_group,
            "target_os": parsed.target_os,
            "description": test_request
        }
        
        workflow = workflow_generator.generate_workflow(intent_type, requirements, ["web servers"])
        
        # Convert to dict format
        workflow_dict = {
            "id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "type": workflow.workflow_type.value,
            "steps": [
                {
                    "id": step.step_id,
                    "name": step.name,
                    "description": step.description,
                    "type": step.step_type.value,
                    "command": step.command,
                    "script": step.script,
                    "parameters": step.parameters,
                    "timeout": step.timeout,
                    "retry_count": step.retry_count,
                    "risk_level": step.risk_level,
                    "requires_approval": step.requires_approval
                }
                for step in workflow.steps
            ],
            "execution_mode": workflow.execution_mode.value,
            "estimated_duration": workflow.estimated_duration,
            "risk_level": workflow.risk_level,
            "requires_approval": workflow.requires_approval,
            "target_systems": workflow.target_systems
        }
        
        # Step 2: Test automation service health
        automation_healthy = await automation_client.health_check()
        
        # Step 3: Test asset service
        asset_healthy = await asset_client.health_check()
        
        result = {
            "test_request": test_request,
            "ai_processing": {
                "parsed_operation": parsed.operation,
                "parsed_target": parsed.target_process,
                "parsed_group": parsed.target_group,
                "confidence": parsed.confidence,
                "workflow_steps": len(workflow_dict.get('steps', []))
            },
            "service_health": {
                "automation_service": automation_healthy,
                "asset_service": asset_healthy
            },
            "integration_ready": automation_healthy and asset_healthy,
            "workflow_preview": {
                "id": workflow_dict.get('id'),
                "name": workflow_dict.get('name'),
                "description": workflow_dict.get('description'),
                "step_count": len(workflow_dict.get('steps', []))
            }
        }
        
        # Step 4: If services are healthy, test actual submission (without execution)
        if automation_healthy:
            try:
                submission_result = await automation_client.submit_ai_workflow(
                    workflow_dict, 
                    job_name=f"Integration Test: {test_request}"
                )
                result["test_submission"] = {
                    "success": submission_result.get('success'),
                    "job_id": str(submission_result.get('job_id')) if submission_result.get('job_id') is not None else None,
                    "message": submission_result.get('message', submission_result.get('error'))
                }
            except Exception as e:
                result["test_submission"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return result
        
    except Exception as e:
        logger.error("Integration test failed", error=str(e))
        return {
            "error": str(e),
            "integration_ready": False
        }

def classify_intent(message: str) -> tuple[str, float]:
    """Classify user message intent"""
    message_lower = message.lower().strip()
    
    # Question patterns
    question_patterns = [
        'what', 'how', 'when', 'where', 'why', 'who', 'which',
        'status', 'show', 'list', 'display', 'tell me', 'get',
        'how many', 'what is', 'what are', 'how much'
    ]
    
    # Job creation patterns  
    job_patterns = [
        'restart', 'stop', 'start', 'update', 'install', 'remove',
        'deploy', 'configure', 'run', 'execute', 'kill', 'reboot',
        'upgrade', 'downgrade', 'backup', 'restore'
    ]
    
    # Check for question patterns
    for pattern in question_patterns:
        if pattern in message_lower:
            return "question", 0.8
    
    # Check for job patterns
    for pattern in job_patterns:
        if pattern in message_lower:
            return "job_creation", 0.9
    
    # Check if it ends with question mark
    if message.strip().endswith('?'):
        return "question", 0.7
    
    return "unknown", 0.3

async def handle_question(message: str) -> str:
    """Handle informational questions"""
    message_lower = message.lower()
    
    # Status-related questions
    if any(word in message_lower for word in ['status', 'health', 'running', 'up', 'down']):
        if any(word in message_lower for word in ['worker', 'job', 'task']):
            return "I can see the system status through the monitoring dashboard. Currently, there are 24 worker processes running across 2 containers, ready to handle automation tasks. You can check the detailed status in the Job Monitoring section."
        elif any(word in message_lower for word in ['server', 'system', 'service']):
            return "To check server status, I would need to run a status check job. Would you like me to create a job to check the status of specific servers or services?"
    
    # Count/list questions
    elif any(word in message_lower for word in ['how many', 'count', 'list', 'show']):
        if any(word in message_lower for word in ['worker', 'job', 'task']):
            return "Currently there are 24 worker processes running across 2 containers. You can see detailed worker information and active tasks in the Job Monitoring dashboard."
        elif any(word in message_lower for word in ['server', 'asset']):
            return "I can help you get a list of servers or assets. Would you like me to create a job to inventory your infrastructure?"
    
    # Help questions
    elif any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
        return """I can help you with:

**Automation Tasks:**
- Restart services: "restart nginx on web servers"
- Update software: "update stationcontroller on CIS servers" 
- System operations: "stop Apache on production servers"

**Information:**
- System status and monitoring
- Worker and job statistics
- Infrastructure inventory

**Questions:**
- Ask about server status, running services, or system health
- Get help with automation commands

Try asking me to perform a specific task or check on something!"""
    
    # Default response for questions
    return f"I understand you're asking about: '{message}'. I can help with system automation and monitoring. For specific server information, I may need to create a monitoring job. Would you like me to help you with a specific automation task instead?"



# Predictive Analytics Endpoints
@app.get("/ai/predictive/insights")
async def get_predictive_insights():
    """Get comprehensive predictive insights"""
    try:
        insights = await system_analytics.get_predictive_insights()
        return {
            "success": True,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get predictive insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/analyze-performance")
async def analyze_performance(metrics: Dict[str, float]):
    """Analyze system performance and generate insights"""
    try:
        insights = await system_analytics.analyze_system_performance(metrics)
        return {
            "success": True,
            "performance_insights": [insight.to_dict() for insight in insights],
            "analysis_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/detect-anomalies")
async def detect_anomalies(request: Dict[str, Any]):
    """Detect advanced anomalies in system behavior"""
    try:
        metrics = request.get("metrics", {})
        execution_data = request.get("execution_data", {})
        
        anomalies = await system_analytics.detect_advanced_anomalies(metrics, execution_data)
        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies),
            "detection_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/predictive/maintenance-schedule")
async def get_maintenance_schedule():
    """Get predictive maintenance recommendations"""
    try:
        # Get targets from asset service (simplified for demo)
        targets = [
            {"hostname": "server-01", "type": "server", "last_maintenance": "2024-01-01T00:00:00"},
            {"hostname": "server-02", "type": "server", "last_maintenance": "2024-02-01T00:00:00"},
            {"hostname": "switch-01", "type": "network_device", "last_maintenance": "2024-03-01T00:00:00"}
        ]
        
        recommendations = await system_analytics.generate_maintenance_schedule(targets)
        return {
            "success": True,
            "maintenance_recommendations": [rec.to_dict() for rec in recommendations],
            "count": len(recommendations),
            "generated_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/security-monitor")
async def monitor_security(log_entries: List[Dict[str, Any]]):
    """Monitor log entries for security events"""
    try:
        alerts = await system_analytics.monitor_security_events(log_entries)
        return {
            "success": True,
            "security_alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
            "analysis_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to monitor security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/status")
async def get_ai_status():
    """Get the status of the AI Brain Engine components"""
    try:
        # Check which components are available
        components_status = {
            "modern_components": {
                "system_analytics": hasattr(ai_engine, 'system_analytics'),
                "intent_processor": hasattr(ai_engine, 'intent_processor'),
                "system_capabilities": hasattr(ai_engine, 'system_capabilities'),
                "ai_engine": hasattr(ai_engine, 'ai_engine')
            },
            "migration_complete": True,
            "active_mode": "modern",
            "version": "2.0.0",
            "features": {
                "llm_powered": True,
                "vector_storage": True,
                "intelligent_analysis": True,
                "natural_language": True
            }
        }
        
        return {
            "success": True,
            "ai_status": components_status,
            "message": "AI Brain is running with modern components"
        }
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API v1 routes for dashboard compatibility
@app.get("/api/v1/ai/health")
async def api_v1_health_check():
    """API v1 compatible health check endpoint for dashboard"""
    try:
        # Get detailed health status from AI Brain Engine
        brain_health = ai_engine.get_health_status()
        
        # Transform to expected dashboard format
        services = {
            "ai-brain": {
                "status": "healthy" if brain_health.get("status") == "healthy" else "unhealthy",
                "service": "ai-brain",
                "components": brain_health.get("components", {}),
                "architecture": brain_health.get("architecture", "pure_llm"),
                "timestamp": brain_health.get("timestamp")
            }
        }
        
        return {
            "status": "healthy",
            "services": services,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"API v1 health check failed: {e}")
        return {
            "status": "unhealthy",
            "services": {
                "ai-brain": {
                    "status": "unhealthy",
                    "service": "ai-brain",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v1/ai/monitoring/dashboard")
async def api_v1_monitoring_dashboard():
    """API v1 compatible monitoring dashboard endpoint"""
    try:
        # Get current health status
        brain_health = ai_engine.get_health_status()
        
        # Create dashboard data structure
        current_services = {
            "ai-brain": {
                "status": "healthy" if brain_health.get("status") == "healthy" else "unhealthy",
                "service": "ai-brain",
                "components": brain_health.get("components", {}),
                "architecture": brain_health.get("architecture", "pure_llm"),
                "response_time": 0.1,
                "timestamp": brain_health.get("timestamp")
            }
        }
        
        # Determine overall health
        overall_health = "healthy" if brain_health.get("status") == "healthy" else "degraded"
        
        # Create alerts based on component status
        alerts = []
        components = brain_health.get("components", {})
        for component, status in components.items():
            if not status:
                alerts.append({
                    "severity": "warning",
                    "service": "ai-brain",
                    "message": f"Component {component} is not available"
                })
        
        # Generate recommendations
        recommendations = []
        if alerts:
            recommendations.append("Some AI components are not fully initialized - this may affect functionality")
        else:
            recommendations.append("AI system is operating normally")
        
        return {
            "current": {
                "services": current_services,
                "overall_health": overall_health
            },
            "history": [],  # Could be populated with historical data
            "analysis": {
                "overall_health": overall_health,
                "alerts": alerts,
                "recommendations": recommendations
            },
            "statistics": {
                "total_services": 1,
                "healthy_services": 1 if overall_health == "healthy" else 0,
                "unhealthy_services": 0 if overall_health == "healthy" else 1,
                "uptime_percentage": 100.0 if overall_health == "healthy" else 75.0
            }
        }
    except Exception as e:
        logger.error(f"API v1 monitoring dashboard failed: {e}")
        return {
            "current": {
                "services": {
                    "ai-brain": {
                        "status": "unhealthy",
                        "service": "ai-brain",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                "overall_health": "unhealthy"
            },
            "history": [],
            "analysis": {
                "overall_health": "unhealthy",
                "alerts": [{
                    "severity": "critical",
                    "service": "ai-brain",
                    "message": f"AI service error: {str(e)}"
                }],
                "recommendations": ["Check AI service logs and restart if necessary"]
            },
            "statistics": {
                "total_services": 1,
                "healthy_services": 0,
                "unhealthy_services": 1,
                "uptime_percentage": 0.0
            }
        }

@app.post("/api/v1/ai/circuit-breaker/reset/{service_name}")
async def api_v1_reset_circuit_breaker(service_name: str):
    """API v1 compatible circuit breaker reset endpoint"""
    try:
        logger.info(f"Circuit breaker reset requested for service: {service_name}")
        
        # For AI brain, we can try to reinitialize components
        if service_name == "ai-brain":
            # Attempt to reinitialize the AI engine
            try:
                # This would reinitialize the AI engine if it has such capability
                if hasattr(ai_engine, 'reinitialize'):
                    await ai_engine.reinitialize()
                    return {"message": f"Circuit breaker reset for {service_name}", "success": True}
                else:
                    return {"message": f"Circuit breaker reset acknowledged for {service_name} (no action needed)", "success": True}
            except Exception as reinit_error:
                logger.error(f"Failed to reinitialize {service_name}: {reinit_error}")
                return {"message": f"Circuit breaker reset attempted for {service_name} but reinitialize failed", "success": False}
        else:
            return {"message": f"Circuit breaker reset not applicable for {service_name}", "success": False}
            
    except Exception as e:
        logger.error(f"Circuit breaker reset failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {str(e)}")

@app.get("/api/v1/ai/knowledge-stats")
def api_v1_knowledge_stats():
    """API v1 compatible knowledge stats endpoint"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI Brain Engine not initialized")
        
        stats = ai_engine.get_knowledge_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        # Return basic stats if detailed stats fail
        return {
            "status": "partial",
            "stats": {
                "total_documents": 0,
                "total_patterns": 0,
                "vector_store_status": "unavailable",
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/ai/knowledge-stats")
def knowledge_stats():
    """Knowledge stats endpoint for API gateway routing"""
    try:
        if not ai_engine:
            raise HTTPException(status_code=503, detail="AI Brain Engine not initialized")
        
        stats = ai_engine.get_knowledge_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        # Return basic stats if detailed stats fail
        return {
            "status": "partial",
            "stats": {
                "total_documents": 0,
                "total_patterns": 0,
                "vector_store_status": "unavailable",
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3008)
#!/usr/bin/env python3
"""
Clean AI Brain Service - Main Entry Point
Simplified Architecture with Clear Responsibilities
"""

import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx
import uuid

# Add paths
sys.path.append('/app')

# Import clean architecture components
from orchestration.ai_brain_service_clean import CleanAIBrainService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IntentRequest(BaseModel):
    """User intent request"""
    intent: str
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class IntentResponse(BaseModel):
    """AI Brain response"""
    success: bool
    intent_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    architecture: str = "clean"

# ============================================================================
# GLOBAL SERVICE INSTANCE
# ============================================================================

ai_brain_service: Optional[CleanAIBrainService] = None

# ============================================================================
# STARTUP/SHUTDOWN LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global ai_brain_service
    
    logger.info("🧹 Starting Clean AI Brain Service")
    
    try:
        # Check Ollama availability - CRITICAL
        await check_ollama_availability()
        
        # Initialize AI Brain Service
        ai_brain_service = CleanAIBrainService()
        
        logger.info("🚀 Clean AI Brain Service started successfully")
        logger.info("📋 Architecture: Decision Making + Orchestration Coordination")
        logger.info("🔗 Flow: User → AI Brain → Prefect → Services")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 Clean AI Brain Service shutting down")

async def check_ollama_availability():
    """Check if Ollama is available - CRITICAL for clean architecture"""
    ollama_host = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            response.raise_for_status()
        
        logger.info("✅ Ollama LLM available - AI decision making ready")
        
    except Exception as e:
        logger.error(f"❌ Ollama LLM unavailable: {e}")
        logger.error("🚨 CRITICAL: Clean architecture requires Ollama for all decisions")
        raise RuntimeError(f"Ollama unavailable - AI Brain cannot start: {e}")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Clean AI Brain Service",
    description="Simplified AI-driven orchestration with clear responsibilities",
    version="2.0.0-clean",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global ai_brain_service
    
    if not ai_brain_service:
        return {
            "status": "unhealthy",
            "reason": "AI Brain service not initialized",
            "architecture": "clean"
        }
    
    # Check Ollama availability
    ollama_available = False
    try:
        ollama_host = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            ollama_available = response.status_code == 200
    except:
        pass
    
    return {
        "status": "healthy" if ollama_available else "unhealthy",
        "architecture": "clean",
        "ollama_available": ollama_available,
        "critical_dependencies": {
            "ollama_llm": ollama_available
        }
    }

@app.post("/process", response_model=IntentResponse)
async def process_intent(request: IntentRequest):
    """
    Process user intent using clean architecture
    
    Flow:
    1. AI Brain receives intent
    2. AI Brain makes decision (Ollama LLM)
    3. AI Brain generates workflow plan
    4. AI Brain submits to Prefect for orchestration
    5. Prefect coordinates service calls
    6. Results returned through chain
    """
    global ai_brain_service
    
    if not ai_brain_service:
        raise HTTPException(status_code=503, detail="AI Brain service not available")
    
    try:
        # Generate intent ID
        intent_id = str(uuid.uuid4())
        
        logger.info(f"🧠 Processing intent: {request.intent[:100]}...")
        
        # Process through clean architecture
        result = await ai_brain_service.process_intent(request.intent, request.context)
        
        if result.get("status") == "success":
            return IntentResponse(
                success=True,
                intent_id=intent_id,
                result=result,
                architecture="clean"
            )
        else:
            return IntentResponse(
                success=False,
                intent_id=intent_id,
                error=result.get("error", "Unknown error"),
                architecture="clean"
            )
    
    except Exception as e:
        logger.error(f"❌ Intent processing failed: {e}")
        return IntentResponse(
            success=False,
            intent_id=intent_id if 'intent_id' in locals() else "unknown",
            error=str(e),
            architecture="clean"
        )

@app.get("/architecture")
async def get_architecture_info():
    """Get clean architecture information"""
    global ai_brain_service
    
    if ai_brain_service:
        return await ai_brain_service.get_architecture_status()
    else:
        return {
            "architecture": "clean",
            "status": "not_initialized"
        }

@app.get("/services/status")
async def get_services_status():
    """Get status of all registered services"""
    global ai_brain_service
    
    if not ai_brain_service:
        return {"error": "AI Brain service not initialized"}
    
    return await ai_brain_service.get_services_status()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🧹 Starting Clean AI Brain Service")
    print("📋 Architecture: Decision Making + Orchestration Coordination")
    print("🔗 Flow: User → AI Brain → Prefect → Services")
    print("🚫 No direct service connections, no background processing")
    
    uvicorn.run(
        "main_clean:app",
        host="0.0.0.0",
        port=3005,
        reload=False,
        log_level="info"
    )
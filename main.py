#!/usr/bin/env python3
"""
NEWIDEA.MD Pipeline - Main Entry Point
4-Stage AI-Driven Operations Pipeline

Architecture:
User Request → Stage A (Classifier) → Stage B (Selector) → Stage C (Planner) → [Stage D (Answerer)] → Execution

This replaces the old AI Brain with a structured, testable, production-ready pipeline.
CLEAN BREAK - No backward compatibility.
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
from datetime import datetime

# Add paths
sys.path.append('/app')

# Import pipeline components
from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_b.tool_registry import ToolRegistry
from llm.ollama_client import OllamaClient
from pipeline.schemas.decision_v1 import DecisionV1
from pipeline.schemas.selection_v1 import SelectionV1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PipelineRequest(BaseModel):
    """User request to the NEWIDEA.MD pipeline"""
    request: str
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class PipelineResponse(BaseModel):
    """Pipeline response"""
    success: bool
    request_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    architecture: str = "newidea-pipeline"
    pipeline_version: str = "1.0.0"

# ============================================================================
# GLOBAL PIPELINE INSTANCE
# ============================================================================

stage_a_classifier: Optional[StageAClassifier] = None
stage_b_selector: Optional[StageBSelector] = None
tool_registry: Optional[ToolRegistry] = None
llm_client: Optional[OllamaClient] = None

# ============================================================================
# STARTUP/SHUTDOWN LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global stage_a_classifier, stage_b_selector, tool_registry, llm_client
    
    logger.info("🚀 Starting NEWIDEA.MD Pipeline")
    logger.info("📋 Architecture: 4-Stage AI Pipeline")
    logger.info("🔗 Flow: User → Stage A → Stage B → Stage C → [Stage D] → Execution")
    
    try:
        # Check Ollama availability - CRITICAL
        await check_ollama_availability()
        
        # Initialize LLM Client
        ollama_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
            "default_model": os.getenv("OLLAMA_MODEL", "llama2"),
            "timeout": 30
        }
        llm_client = OllamaClient(ollama_config)
        await llm_client.connect()
        
        # Initialize Tool Registry
        tool_registry = ToolRegistry()
        
        # Initialize Stage A Classifier
        stage_a_classifier = StageAClassifier(llm_client)
        
        # Initialize Stage B Selector
        stage_b_selector = StageBSelector(llm_client, tool_registry)
        
        logger.info("✅ NEWIDEA.MD Pipeline started successfully")
        logger.info("🏗️  Phase 1: Stage A Classifier - READY")
        logger.info("🏗️  Phase 2: Stage B Selector - READY")
        logger.info("⏳ Phase 3: Stage C Planner - Coming Next")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        # Continue startup even if Ollama is not available for development
        logger.warning("⚠️  Continuing startup without LLM - limited functionality")
        yield
    finally:
        if llm_client:
            await llm_client.disconnect()
        logger.info("🛑 NEWIDEA.MD Pipeline shutting down")

async def check_ollama_availability():
    """Check if Ollama is available - CRITICAL for pipeline"""
    ollama_host = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            response.raise_for_status()
        
        logger.info("✅ Ollama LLM available - Pipeline ready")
        
    except Exception as e:
        logger.error(f"❌ Ollama LLM unavailable: {e}")
        logger.error("🚨 CRITICAL: NEWIDEA.MD pipeline requires Ollama for all stages")
        raise RuntimeError(f"Ollama unavailable - Pipeline cannot start: {e}")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="NEWIDEA.MD Pipeline",
    description="4-Stage AI-Driven Operations Pipeline - Clean Break Architecture",
    version="1.0.0-newidea",
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
    global stage_a_classifier, stage_b_selector, llm_client
    
    # Check Ollama availability
    ollama_available = False
    stage_a_healthy = False
    stage_b_healthy = False
    
    try:
        if llm_client:
            ollama_available = await llm_client.health_check()
        
        if stage_a_classifier and ollama_available:
            health_status = await stage_a_classifier.health_check()
            stage_a_healthy = health_status["stage_a"] == "healthy"
            
        if stage_b_selector and ollama_available:
            health_status = await stage_b_selector.health_check()
            stage_b_healthy = health_status["stage_b_selector"] == "healthy"
    except:
        pass
    
    return {
        "status": "healthy" if (ollama_available and stage_a_healthy and stage_b_healthy) else "degraded",
        "architecture": "newidea-pipeline",
        "version": "1.0.0",
        "phase": "Phase 2 - Stage B Selector",
        "next_phase": "Phase 3 - Stage C Planner",
        "ollama_available": ollama_available,
        "pipeline_stages": {
            "stage_a_classifier": "✅ Implemented" if stage_a_healthy else "⚠️ Degraded",
            "stage_b_selector": "✅ Implemented" if stage_b_healthy else "⚠️ Degraded", 
            "stage_c_planner": "Not implemented",
            "stage_d_answerer": "Not implemented"
        },
        "critical_dependencies": {
            "ollama_llm": ollama_available,
            "stage_a_classifier": stage_a_healthy,
            "stage_b_selector": stage_b_healthy
        }
    }

@app.post("/process", response_model=PipelineResponse)
async def process_request(request: PipelineRequest):
    """
    Process user request through NEWIDEA.MD pipeline
    
    Flow:
    1. Stage A: Classify intent and extract entities
    2. Stage B: Select tools and assess risk
    3. Stage C: Generate execution plan with safety
    4. [Stage D: Information retrieval if needed]
    5. Execute with monitoring and rollback
    """
    global stage_a_classifier, stage_b_selector
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    logger.info(f"🔄 Processing request: {request.request[:100]}...")
    
    try:
        if not stage_a_classifier:
            raise HTTPException(
                status_code=503,
                detail="Stage A Classifier not available - LLM backend required"
            )
        
        if not stage_b_selector:
            raise HTTPException(
                status_code=503,
                detail="Stage B Selector not available - LLM backend required"
            )
        
        # Prepare context
        context = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "request_id": request_id,
            **request.context
        }
        
        # Stage A: Classify the request
        decision = await stage_a_classifier.classify(request.request, context)
        
        logger.info(f"✅ Stage A complete: {decision.intent.category}/{decision.intent.action}")
        logger.info(f"📊 Confidence: {decision.confidence_level.value} ({decision.overall_confidence:.2f})")
        logger.info(f"⚠️  Risk: {decision.risk_level.value}")
        
        # Stage B: Select tools and determine policy
        selection = await stage_b_selector.select_tools(decision, context)
        
        logger.info(f"✅ Stage B complete: {selection.total_tools} tools selected")
        logger.info(f"🔧 Tools: {', '.join([tool.tool_name for tool in selection.selected_tools])}")
        logger.info(f"📋 Policy: {selection.policy.risk_level.value} risk, approval={selection.policy.requires_approval}")
        
        # Convert to dicts for response
        decision_dict = decision.model_dump()
        selection_dict = selection.model_dump()
        
        return PipelineResponse(
            success=True,
            request_id=request_id,
            result={
                "stage": "stage_b_complete",
                "decision": decision_dict,
                "selection": selection_dict,
                "next_stage": selection.next_stage,
                "message": f"Selected {selection.total_tools} tools for {decision.intent.category}/{decision.intent.action}",
                "phase": "Phase 2 - Stage B Selector",
                "timestamp": datetime.utcnow().isoformat()
            },
            architecture="newidea-pipeline"
        )
        
    except Exception as e:
        logger.error(f"❌ Pipeline processing failed: {e}")
        return PipelineResponse(
            success=False,
            request_id=request_id,
            error=str(e),
            architecture="newidea-pipeline"
        )

@app.get("/stage-a/capabilities")
async def get_stage_a_capabilities():
    """Get Stage A capabilities"""
    global stage_a_classifier
    
    if not stage_a_classifier:
        raise HTTPException(
            status_code=503,
            detail="Stage A Classifier not available"
        )
    
    return await stage_a_classifier.get_capabilities()

@app.get("/stage-a/health")
async def get_stage_a_health():
    """Get Stage A health status"""
    global stage_a_classifier
    
    if not stage_a_classifier:
        raise HTTPException(
            status_code=503,
            detail="Stage A Classifier not available"
        )
    
    return await stage_a_classifier.health_check()

@app.get("/stage-b/capabilities")
async def get_stage_b_capabilities():
    """Get Stage B capabilities"""
    global stage_b_selector
    
    if not stage_b_selector:
        raise HTTPException(
            status_code=503,
            detail="Stage B Selector not available"
        )
    
    return stage_b_selector.get_capabilities()

@app.get("/stage-b/health")
async def get_stage_b_health():
    """Get Stage B health status"""
    global stage_b_selector
    
    if not stage_b_selector:
        raise HTTPException(
            status_code=503,
            detail="Stage B Selector not available"
        )
    
    return await stage_b_selector.health_check()

@app.get("/stage-b/tools")
async def get_available_tools():
    """Get available tools in the tool registry"""
    global tool_registry
    
    if not tool_registry:
        raise HTTPException(
            status_code=503,
            detail="Tool Registry not available"
        )
    
    tools = tool_registry.get_all_tools()
    return {
        "total_tools": len(tools),
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "capabilities": [cap.name for cap in tool.capabilities],
                "permissions": tool.permissions.value,
                "production_safe": tool.production_safe,
                "max_execution_time": tool.max_execution_time
            }
            for tool in tools
        ],
        "registry_stats": tool_registry.get_registry_stats()
    }

@app.get("/architecture")
async def get_architecture_info():
    """Get NEWIDEA.MD pipeline architecture information"""
    return {
        "architecture": "newidea-pipeline",
        "version": "1.0.0",
        "description": "4-Stage AI-Driven Operations Pipeline",
        "stages": {
            "stage_a": {
                "name": "Classifier",
                "purpose": "Intent classification and entity extraction",
                "output": "Decision v1 JSON",
                "status": "✅ Implemented"
            },
            "stage_b": {
                "name": "Selector", 
                "purpose": "Tool selection and risk assessment",
                "output": "Selection v1 JSON",
                "status": "✅ Implemented"
            },
            "stage_c": {
                "name": "Planner",
                "purpose": "Execution planning with safety mechanisms",
                "output": "Plan v1 JSON with DAG",
                "status": "Not implemented"
            },
            "stage_d": {
                "name": "Answerer",
                "purpose": "Information retrieval and RAG",
                "output": "Answer v1 JSON",
                "status": "Not implemented"
            }
        },
        "flow": "User → Stage A → Stage B → Stage C → [Stage D] → Execution",
        "features": {
            "json_validation": "Built-in validation and repair",
            "risk_assessment": "Automatic risk level calculation",
            "approval_workflows": "Production approval mechanisms",
            "safety_mechanisms": "Rollback and failure detection",
            "dag_execution": "Parallel execution with dependencies",
            "audit_trails": "Complete operation logging"
        },
        "phase": "Phase 2 - Stage B Selector Complete",
        "next_milestone": "Phase 3 - Stage C Planner Implementation"
    }

@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get detailed pipeline implementation status"""
    return {
        "implementation_status": {
            "phase_0_foundation": {
                "status": "complete",
                "completion_date": datetime.utcnow().isoformat(),
                "components": {
                    "directory_structure": "✅ Complete",
                    "schemas": "✅ Decision v1 schema created",
                    "foundation_files": "✅ All __init__.py files created",
                    "main_entry_point": "✅ FastAPI app created",
                    "old_ai_brain": "⏳ Removal pending"
                }
            },
            "phase_1_stage_a": {
                "status": "pending",
                "estimated_duration": "4-5 days",
                "test_cases": "75 tests planned"
            },
            "phase_2_stage_b": {
                "status": "pending", 
                "estimated_duration": "4-5 days",
                "test_cases": "60 tests planned"
            },
            "phase_3_stage_c": {
                "status": "pending",
                "estimated_duration": "5-6 days", 
                "test_cases": "80 tests planned"
            },
            "phase_4_stage_d": {
                "status": "pending",
                "estimated_duration": "3-4 days",
                "test_cases": "30 tests planned"
            },
            "phase_5_orchestration": {
                "status": "pending",
                "estimated_duration": "4-5 days",
                "test_cases": "50 tests planned"
            },
            "phase_6_production": {
                "status": "pending",
                "estimated_duration": "3-4 days",
                "test_cases": "Integration tests"
            }
        },
        "total_estimated_duration": "28-32 days",
        "total_test_cases": "300+ tests"
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting NEWIDEA.MD Pipeline")
    print("📋 Architecture: 4-Stage AI Pipeline")
    print("🔗 Flow: User → Stage A → Stage B → Stage C → [Stage D] → Execution")
    print("🏗️  Phase 0: Foundation Complete")
    print("⏳ Phase 1: Stage A Classifier - Coming Next")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3005,
        reload=False,
        log_level="info"
    )
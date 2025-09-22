#!/usr/bin/env python3
"""
OpsConductor Network Analyzer Service
Provides comprehensive packet analysis and network troubleshooting capabilities
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

import structlog
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add shared directory to path
sys.path.append('/app/shared')

from base_service import BaseService
from rbac_middleware import RBACMiddleware, require_permission

# Import our analyzer modules
from analyzers.packet_analyzer import PacketAnalyzer
from analyzers.network_monitor import NetworkMonitor
from analyzers.protocol_analyzer import ProtocolAnalyzer
from analyzers.ai_analyzer import AINetworkAnalyzer
from agents.remote_agent import RemoteAnalysisAgent
from models.analysis_models import *
from utils.websocket_manager import WebSocketManager

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

logger = structlog.get_logger(__name__)

class NetworkAnalyzerService(BaseService):
    """Network Analyzer Service with comprehensive packet analysis capabilities"""
    
    def __init__(self):
        super().__init__(
            service_name="network-analyzer-service",
            service_port=3006,
            db_schema="network_analysis"
        )
        
        # Initialize analyzers
        self.packet_analyzer = PacketAnalyzer()
        self.network_monitor = NetworkMonitor()
        self.protocol_analyzer = ProtocolAnalyzer()
        self.ai_analyzer = AINetworkAnalyzer()
        self.remote_agent = RemoteAnalysisAgent()
        
        # WebSocket manager for real-time updates
        self.websocket_manager = WebSocketManager()
        
        # Active analysis sessions
        self.active_sessions: Dict[str, Dict] = {}

# Global service instance
service = NetworkAnalyzerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Network Analyzer Service")
    
    # Initialize service
    await service.initialize()
    
    # Start background monitoring
    asyncio.create_task(service.network_monitor.start_monitoring())
    
    yield
    
    logger.info("Shutting down Network Analyzer Service")
    await service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="OpsConductor Network Analyzer Service",
    description="Comprehensive network packet analysis and troubleshooting service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add RBAC middleware
rbac = RBACMiddleware(service.identity_service_url)
app.add_middleware(rbac.middleware_class)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = await service.check_db_connection()
        
        # Check Redis connection
        redis_status = await service.check_redis_connection()
        
        # Check analyzer status
        analyzer_status = {
            "packet_analyzer": service.packet_analyzer.is_ready(),
            "network_monitor": service.network_monitor.is_running(),
            "ai_analyzer": service.ai_analyzer.is_ready()
        }
        
        return {
            "status": "healthy",
            "service": "network-analyzer-service",
            "version": "1.0.0",
            "database": db_status,
            "redis": redis_status,
            "analyzers": analyzer_status,
            "active_sessions": len(service.active_sessions)
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Packet Analysis Endpoints
@app.post("/api/v1/analysis/start-capture", response_model=CaptureSessionResponse)
async def start_packet_capture(
    request: StartCaptureRequest,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """Start a packet capture session"""
    try:
        session_id = await service.packet_analyzer.start_capture(
            interface=request.interface,
            filter_expression=request.filter_expression,
            duration=request.duration,
            packet_count=request.packet_count,
            target_id=request.target_id
        )
        
        # Store session info
        service.active_sessions[session_id] = {
            "type": "capture",
            "user_id": user_info["user_id"],
            "started_at": asyncio.get_event_loop().time(),
            "request": request.dict()
        }
        
        # Start background analysis if AI analysis is enabled
        if request.enable_ai_analysis:
            background_tasks.add_task(
                service.ai_analyzer.analyze_capture_session,
                session_id
            )
        
        logger.info("Started packet capture session", 
                   session_id=session_id, 
                   user_id=user_info["user_id"])
        
        return CaptureSessionResponse(
            session_id=session_id,
            status="started",
            message="Packet capture session started successfully"
        )
        
    except Exception as e:
        logger.error("Failed to start packet capture", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analysis/capture/{session_id}", response_model=CaptureResultResponse)
async def get_capture_results(
    session_id: str,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """Get results from a packet capture session"""
    try:
        if session_id not in service.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        results = await service.packet_analyzer.get_capture_results(session_id)
        
        return CaptureResultResponse(
            session_id=session_id,
            status=results["status"],
            packet_count=results["packet_count"],
            packets=results["packets"],
            statistics=results["statistics"],
            ai_analysis=results.get("ai_analysis")
        )
        
    except Exception as e:
        logger.error("Failed to get capture results", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/stop-capture/{session_id}")
async def stop_packet_capture(
    session_id: str,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_WRITE"))
):
    """Stop a packet capture session"""
    try:
        if session_id not in service.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await service.packet_analyzer.stop_capture(session_id)
        
        # Clean up session
        del service.active_sessions[session_id]
        
        logger.info("Stopped packet capture session", 
                   session_id=session_id, 
                   user_id=user_info["user_id"])
        
        return {"status": "stopped", "session_id": session_id}
        
    except Exception as e:
        logger.error("Failed to stop packet capture", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Network Monitoring Endpoints
@app.get("/api/v1/monitoring/status", response_model=NetworkStatusResponse)
async def get_network_status(
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """Get current network monitoring status"""
    try:
        status = await service.network_monitor.get_current_status()
        
        return NetworkStatusResponse(
            interfaces=status["interfaces"],
            traffic_stats=status["traffic_stats"],
            active_connections=status["active_connections"],
            alerts=status["alerts"],
            timestamp=status["timestamp"]
        )
        
    except Exception as e:
        logger.error("Failed to get network status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/monitoring/alerts/configure")
async def configure_network_alerts(
    config: NetworkAlertConfig,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_WRITE"))
):
    """Configure network monitoring alerts"""
    try:
        await service.network_monitor.configure_alerts(config.dict())
        
        logger.info("Configured network alerts", 
                   user_id=user_info["user_id"],
                   config=config.dict())
        
        return {"status": "configured", "message": "Network alerts configured successfully"}
        
    except Exception as e:
        logger.error("Failed to configure network alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Protocol Analysis Endpoints
@app.post("/api/v1/analysis/protocol", response_model=ProtocolAnalysisResponse)
async def analyze_protocol(
    request: ProtocolAnalysisRequest,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """Analyze specific network protocols"""
    try:
        analysis = await service.protocol_analyzer.analyze_protocol(
            protocol=request.protocol,
            data_source=request.data_source,
            filters=request.filters
        )
        
        return ProtocolAnalysisResponse(
            protocol=request.protocol,
            analysis_results=analysis["results"],
            statistics=analysis["statistics"],
            recommendations=analysis["recommendations"],
            timestamp=analysis["timestamp"]
        )
        
    except Exception as e:
        logger.error("Failed to analyze protocol", 
                    protocol=request.protocol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# AI Analysis Endpoints
@app.post("/api/v1/analysis/ai-diagnose", response_model=AIDiagnosisResponse)
async def ai_network_diagnosis(
    request: AIDiagnosisRequest,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """AI-powered network diagnosis and troubleshooting"""
    try:
        diagnosis = await service.ai_analyzer.diagnose_network_issue(
            symptoms=request.symptoms,
            network_data=request.network_data,
            context=request.context
        )
        
        # If automated remediation is requested, queue it
        if request.enable_auto_remediation and diagnosis.get("remediation_available"):
            background_tasks.add_task(
                service.ai_analyzer.execute_remediation,
                diagnosis["remediation_plan"],
                user_info["user_id"]
            )
        
        return AIDiagnosisResponse(
            diagnosis_id=diagnosis["diagnosis_id"],
            issue_type=diagnosis["issue_type"],
            confidence_score=diagnosis["confidence_score"],
            root_cause=diagnosis["root_cause"],
            recommendations=diagnosis["recommendations"],
            remediation_plan=diagnosis.get("remediation_plan"),
            supporting_evidence=diagnosis["supporting_evidence"]
        )
        
    except Exception as e:
        logger.error("Failed to perform AI diagnosis", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Remote Analysis Endpoints
@app.post("/api/v1/remote/deploy-agent")
async def deploy_remote_agent(
    request: DeployAgentRequest,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_WRITE"))
):
    """Deploy analysis agent to remote target"""
    try:
        agent_id = await service.remote_agent.deploy_agent(
            target_id=request.target_id,
            agent_config=request.agent_config
        )
        
        logger.info("Deployed remote analysis agent", 
                   agent_id=agent_id,
                   target_id=request.target_id,
                   user_id=user_info["user_id"])
        
        return {
            "agent_id": agent_id,
            "status": "deployed",
            "message": "Remote analysis agent deployed successfully"
        }
        
    except Exception as e:
        logger.error("Failed to deploy remote agent", 
                    target_id=request.target_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/remote/analyze/{agent_id}")
async def remote_network_analysis(
    agent_id: str,
    request: RemoteAnalysisRequest,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """Execute network analysis on remote target"""
    try:
        results = await service.remote_agent.execute_analysis(
            agent_id=agent_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters
        )
        
        return {
            "agent_id": agent_id,
            "analysis_type": request.analysis_type,
            "results": results,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error("Failed to execute remote analysis", 
                    agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/analysis/{session_id}")
async def websocket_analysis_updates(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time analysis updates"""
    await service.websocket_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and send updates
            await asyncio.sleep(1)
            
            # Send periodic updates if session is active
            if session_id in service.active_sessions:
                update = await service.packet_analyzer.get_session_update(session_id)
                if update:
                    await service.websocket_manager.send_update(session_id, update)
                    
    except WebSocketDisconnect:
        service.websocket_manager.disconnect(session_id)

# Session Management Endpoints
@app.get("/api/v1/sessions", response_model=List[AnalysisSessionInfo])
async def list_analysis_sessions(
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_READ"))
):
    """List all active analysis sessions"""
    try:
        sessions = []
        for session_id, session_info in service.active_sessions.items():
            sessions.append(AnalysisSessionInfo(
                session_id=session_id,
                session_type=session_info["type"],
                user_id=session_info["user_id"],
                started_at=session_info["started_at"],
                status="active"
            ))
        
        return sessions
        
    except Exception as e:
        logger.error("Failed to list analysis sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/sessions/{session_id}")
async def delete_analysis_session(
    session_id: str,
    user_info: dict = Depends(require_permission("NETWORK_ANALYSIS_WRITE"))
):
    """Delete an analysis session"""
    try:
        if session_id not in service.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Stop any active capture
        await service.packet_analyzer.stop_capture(session_id)
        
        # Clean up session
        del service.active_sessions[session_id]
        
        logger.info("Deleted analysis session", 
                   session_id=session_id,
                   user_id=user_info["user_id"])
        
        return {"status": "deleted", "session_id": session_id}
        
    except Exception as e:
        logger.error("Failed to delete analysis session", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3006,
        reload=True,
        log_config=None  # Use structlog configuration
    )
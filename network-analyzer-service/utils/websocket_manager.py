"""
WebSocket Manager for real-time network analysis updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection"""
        try:
            await websocket.accept()
            
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            
            self.active_connections[session_id].append(websocket)
            self.connection_metadata[websocket] = {
                "session_id": session_id,
                "connected_at": datetime.now(),
                "last_ping": datetime.now()
            }
            
            logger.info("WebSocket connected", 
                       session_id=session_id,
                       total_connections=len(self.active_connections[session_id]))
            
            # Send welcome message
            await self.send_personal_message(websocket, {
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to connect WebSocket", 
                        session_id=session_id, error=str(e))
    
    def disconnect(self, session_id: str, websocket: Optional[WebSocket] = None):
        """Disconnect a WebSocket"""
        try:
            if websocket:
                # Disconnect specific websocket
                if session_id in self.active_connections:
                    if websocket in self.active_connections[session_id]:
                        self.active_connections[session_id].remove(websocket)
                    
                    # Clean up empty session
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]
                
                # Clean up metadata
                if websocket in self.connection_metadata:
                    del self.connection_metadata[websocket]
                
                logger.info("WebSocket disconnected", 
                           session_id=session_id)
            else:
                # Disconnect all websockets for session
                if session_id in self.active_connections:
                    for ws in self.active_connections[session_id]:
                        if ws in self.connection_metadata:
                            del self.connection_metadata[ws]
                    
                    del self.active_connections[session_id]
                
                logger.info("All WebSockets disconnected for session", 
                           session_id=session_id)
        
        except Exception as e:
            logger.error("Error during WebSocket disconnect", 
                        session_id=session_id, error=str(e))
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning("Failed to send personal message", error=str(e))
            # Remove disconnected websocket
            self._cleanup_disconnected_websocket(websocket)
    
    async def send_update(self, session_id: str, update: Dict[str, Any]):
        """Send update to all WebSockets in a session"""
        if session_id not in self.active_connections:
            return
        
        message = {
            "type": "analysis_update",
            "session_id": session_id,
            "data": update,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connections in the session
        disconnected_websockets = []
        
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.warning("Failed to send update to WebSocket", 
                              session_id=session_id, error=str(e))
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self._cleanup_disconnected_websocket(websocket)
    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast alert to all connected WebSockets"""
        message = {
            "type": "network_alert",
            "data": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_websockets = []
        
        for session_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.warning("Failed to broadcast alert", 
                                  session_id=session_id, error=str(e))
                    disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self._cleanup_disconnected_websocket(websocket)
    
    async def send_analysis_complete(self, session_id: str, results: Dict[str, Any]):
        """Send analysis completion notification"""
        message = {
            "type": "analysis_complete",
            "session_id": session_id,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_update(session_id, message)
    
    async def send_error(self, session_id: str, error: str):
        """Send error notification"""
        message = {
            "type": "analysis_error",
            "session_id": session_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_update(session_id, message)
    
    async def ping_connections(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_websockets = []
        
        for session_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(ping_message, default=str))
                    
                    # Update last ping time
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket]["last_ping"] = datetime.now()
                        
                except Exception as e:
                    logger.warning("Failed to ping WebSocket", 
                                  session_id=session_id, error=str(e))
                    disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self._cleanup_disconnected_websocket(websocket)
    
    def _cleanup_disconnected_websocket(self, websocket: WebSocket):
        """Clean up a disconnected WebSocket"""
        try:
            # Find and remove from active connections
            for session_id, websockets in list(self.active_connections.items()):
                if websocket in websockets:
                    websockets.remove(websocket)
                    
                    # Clean up empty sessions
                    if not websockets:
                        del self.active_connections[session_id]
                    
                    break
            
            # Clean up metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
        
        except Exception as e:
            logger.error("Error cleaning up disconnected WebSocket", error=str(e))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        total_connections = sum(len(websockets) for websockets in self.active_connections.values())
        
        session_stats = {}
        for session_id, websockets in self.active_connections.items():
            session_stats[session_id] = {
                "connection_count": len(websockets),
                "connections": []
            }
            
            for websocket in websockets:
                if websocket in self.connection_metadata:
                    metadata = self.connection_metadata[websocket]
                    session_stats[session_id]["connections"].append({
                        "connected_at": metadata["connected_at"].isoformat(),
                        "last_ping": metadata["last_ping"].isoformat()
                    })
        
        return {
            "total_connections": total_connections,
            "active_sessions": len(self.active_connections),
            "session_details": session_stats
        }
    
    async def cleanup_stale_connections(self, max_age_minutes: int = 60):
        """Clean up stale connections"""
        current_time = datetime.now()
        stale_websockets = []
        
        for websocket, metadata in self.connection_metadata.items():
            last_ping = metadata["last_ping"]
            age_minutes = (current_time - last_ping).total_seconds() / 60
            
            if age_minutes > max_age_minutes:
                stale_websockets.append(websocket)
        
        for websocket in stale_websockets:
            logger.info("Cleaning up stale WebSocket connection")
            self._cleanup_disconnected_websocket(websocket)
            
            # Try to close the connection
            try:
                await websocket.close()
            except Exception:
                pass  # Connection might already be closed
        
        if stale_websockets:
            logger.info("Cleaned up stale connections", count=len(stale_websockets))

class WebSocketConnectionManager:
    """Context manager for WebSocket connections"""
    
    def __init__(self, websocket_manager: WebSocketManager, websocket: WebSocket, session_id: str):
        self.websocket_manager = websocket_manager
        self.websocket = websocket
        self.session_id = session_id
    
    async def __aenter__(self):
        await self.websocket_manager.connect(self.websocket, self.session_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.websocket_manager.disconnect(self.session_id, self.websocket)
        
        if exc_type == WebSocketDisconnect:
            logger.info("WebSocket disconnected normally", session_id=self.session_id)
            return True  # Suppress the exception
        
        return False
"""
WebSocket handlers for real-time thinking visualization
"""

import asyncio
import json
import structlog
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Set, Optional, Any
from datetime import datetime

from streaming.redis_thinking_stream import RedisThinkingStreamManager
from streaming.thinking_data_models import StreamConfig, ThinkingContext

logger = structlog.get_logger()


class ThinkingWebSocketManager:
    """Manages WebSocket connections for real-time thinking streams"""
    
    def __init__(self, stream_manager: RedisThinkingStreamManager):
        self.stream_manager = stream_manager
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """Connect a WebSocket to a thinking stream"""
        try:
            await websocket.accept()
            
            # Add to active connections
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            
            self.active_connections[session_id].add(websocket)
            self.connection_sessions[websocket] = session_id
            
            logger.info("🔌 WebSocket connected to thinking stream", 
                       session_id=session_id, 
                       total_connections=len(self.active_connections[session_id]))
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to thinking stream"
            })
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to connect WebSocket", 
                        session_id=session_id, error=str(e))
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        try:
            session_id = self.connection_sessions.get(websocket)
            
            if session_id and session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                
                # Clean up empty session
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            if websocket in self.connection_sessions:
                del self.connection_sessions[websocket]
            
            logger.info("🔌 WebSocket disconnected", session_id=session_id)
            
        except Exception as e:
            logger.error("❌ Error disconnecting WebSocket", error=str(e))
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast a message to all WebSockets connected to a session"""
        try:
            if session_id not in self.active_connections:
                return
            
            connections = self.active_connections[session_id].copy()
            disconnected = []
            
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning("Failed to send to WebSocket", error=str(e))
                    disconnected.append(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected:
                await self.disconnect(websocket)
            
        except Exception as e:
            logger.error("❌ Failed to broadcast to session", 
                        session_id=session_id, error=str(e))
    
    async def stream_thinking_to_websockets(self, session_id: str):
        """Stream thinking steps from Redis to WebSockets"""
        try:
            logger.info("🧠 Starting thinking stream task", session_id=session_id)
            
            if session_id not in self.active_connections:
                logger.warning("🧠 No active connections for session", session_id=session_id)
                return
            
            last_id = "0"
            poll_count = 0
            
            while session_id in self.active_connections:
                poll_count += 1
                
                # Read new messages from Redis stream
                thinking_messages = await self.stream_manager.read_thinking_stream(
                    session_id, last_id, count=10
                )
                
                if thinking_messages:
                    logger.info(f"🧠 Found {len(thinking_messages)} thinking messages", 
                               session_id=session_id, poll_count=poll_count)
                
                for message in thinking_messages:
                    logger.info("🧠 Broadcasting thinking step", 
                               session_id=session_id, message_id=message.get("id"))
                    
                    # Broadcast to WebSockets
                    await self.broadcast_to_session(session_id, {
                        "type": "thinking_step",
                        "data": message
                    })
                    
                    last_id = message["id"]
                
                # Log periodic status
                if poll_count % 100 == 0:
                    logger.debug(f"🧠 Thinking stream polling (count: {poll_count})", 
                                session_id=session_id, last_id=last_id)
                
                # Wait before next poll
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("🧠 Thinking stream task cancelled", session_id=session_id)
            raise
        except Exception as e:
            logger.error("❌ Error streaming thinking to WebSockets", 
                        session_id=session_id, error=str(e))
    
    async def stream_progress_to_websockets(self, session_id: str):
        """Stream progress updates from Redis to WebSockets"""
        try:
            if session_id not in self.active_connections:
                return
            
            last_id = "0"
            
            while session_id in self.active_connections:
                # Read new messages from Redis stream
                progress_messages = await self.stream_manager.read_progress_stream(
                    session_id, last_id, count=10
                )
                
                for message in progress_messages:
                    # Broadcast to WebSockets
                    await self.broadcast_to_session(session_id, {
                        "type": "progress_update",
                        "data": message
                    })
                    
                    last_id = message["id"]
                
                # Wait before next poll
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error("❌ Error streaming progress to WebSockets", 
                        session_id=session_id, error=str(e))
    
    async def handle_websocket_session(self, websocket: WebSocket, session_id: str):
        """Handle a complete WebSocket session"""
        try:
            # Connect WebSocket
            connected = await self.connect(websocket, session_id)
            if not connected:
                return
            
            logger.info("🔌 Starting WebSocket streaming tasks", session_id=session_id)
            
            # Start streaming tasks
            thinking_task = asyncio.create_task(
                self.stream_thinking_to_websockets(session_id)
            )
            progress_task = asyncio.create_task(
                self.stream_progress_to_websockets(session_id)
            )
            
            logger.info("🔌 WebSocket streaming tasks started", session_id=session_id)
            
            try:
                # Keep connection alive and handle incoming messages
                while True:
                    try:
                        # Wait for incoming message or timeout
                        message = await asyncio.wait_for(
                            websocket.receive_json(), timeout=30.0
                        )
                        
                        # Handle client messages
                        await self.handle_client_message(websocket, session_id, message)
                        
                    except asyncio.TimeoutError:
                        # Send keepalive
                        await websocket.send_json({
                            "type": "keepalive",
                            "timestamp": datetime.now().isoformat()
                        })
                        
            except WebSocketDisconnect:
                logger.info("🔌 WebSocket disconnected normally", session_id=session_id)
                
            finally:
                # Cancel streaming tasks
                logger.info("🔌 Cancelling WebSocket streaming tasks", session_id=session_id)
                thinking_task.cancel()
                progress_task.cancel()
                
                # Wait for tasks to complete cancellation
                try:
                    await asyncio.gather(thinking_task, progress_task, return_exceptions=True)
                except Exception:
                    pass
                
                # Disconnect WebSocket
                await self.disconnect(websocket)
                
        except Exception as e:
            logger.error("❌ Error handling WebSocket session", 
                        session_id=session_id, error=str(e))
    
    async def handle_client_message(self, websocket: WebSocket, session_id: str, 
                                  message: Dict[str, Any]):
        """Handle incoming message from WebSocket client"""
        try:
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif message_type == "get_history":
                # Send recent thinking history
                thinking_history = await self.stream_manager.read_thinking_stream(
                    session_id, "0", count=50
                )
                progress_history = await self.stream_manager.read_progress_stream(
                    session_id, "0", count=50
                )
                
                await websocket.send_json({
                    "type": "history",
                    "thinking_history": thinking_history,
                    "progress_history": progress_history
                })
                
            elif message_type == "get_stats":
                # Send session statistics
                stats = await self.stream_manager.get_session_stats(session_id)
                await websocket.send_json({
                    "type": "stats",
                    "data": stats.dict() if stats else None
                })
                
            else:
                logger.warning("Unknown WebSocket message type", 
                              message_type=message_type, session_id=session_id)
                
        except Exception as e:
            logger.error("❌ Error handling client message", 
                        session_id=session_id, error=str(e))


# Global WebSocket manager instance
websocket_manager: Optional[ThinkingWebSocketManager] = None


def initialize_websocket_manager(stream_manager: RedisThinkingStreamManager):
    """Initialize the global WebSocket manager"""
    global websocket_manager
    websocket_manager = ThinkingWebSocketManager(stream_manager)
    logger.info("✅ WebSocket manager initialized")


def get_websocket_manager() -> ThinkingWebSocketManager:
    """Get the global WebSocket manager"""
    if websocket_manager is None:
        raise HTTPException(status_code=500, detail="WebSocket manager not initialized")
    return websocket_manager


# WebSocket endpoint handlers
async def thinking_websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for thinking stream"""
    try:
        if websocket_manager is None:
            await websocket.close(code=1011, reason="WebSocket manager not initialized")
            return
        
        await websocket_manager.handle_websocket_session(websocket, session_id)
    except Exception as e:
        logger.error("❌ Error in thinking WebSocket endpoint", 
                    session_id=session_id, error=str(e))
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


async def progress_websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for progress stream"""
    try:
        if websocket_manager is None:
            await websocket.close(code=1011, reason="WebSocket manager not initialized")
            return
        
        await websocket_manager.handle_websocket_session(websocket, session_id)
    except Exception as e:
        logger.error("❌ Error in progress WebSocket endpoint", 
                    session_id=session_id, error=str(e))
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
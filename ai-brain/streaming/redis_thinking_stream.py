"""
Redis-based streaming infrastructure for real-time thinking visualization
"""

import asyncio
import json
import redis.asyncio as redis
import structlog
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta

from .thinking_data_models import (
    ThinkingStep, ProgressUpdate, StreamMessage, StreamConfig, 
    StreamingSession, StreamStats, ThinkingContext
)

logger = structlog.get_logger()


class RedisThinkingStreamManager:
    """Manages Redis streams for real-time thinking visualization"""
    
    def __init__(self, redis_url: str = "redis://opsconductor-redis:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.active_sessions: Dict[str, StreamingSession] = {}
        self.stream_configs: Dict[str, StreamConfig] = {}
        
    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis thinking stream manager initialized", redis_url=self.redis_url)
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize Redis thinking stream manager", error=str(e))
            return False
    
    async def create_session(self, session_id: str, user_id: str, 
                           config: StreamConfig, context: ThinkingContext) -> StreamingSession:
        """Create a new streaming session"""
        try:
            session = StreamingSession(
                session_id=session_id,
                user_id=user_id,
                config=config,
                context=context
            )
            
            self.active_sessions[session_id] = session
            self.stream_configs[session_id] = config
            
            # Create Redis streams
            thinking_stream = f"{config.thinking_stream_name}:{session_id}"
            progress_stream = f"{config.progress_stream_name}:{session_id}"
            
            # Initialize streams with a startup message
            startup_message = {
                "type": "session_start",
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "debug_mode": str(config.debug_mode),
                "context": json.dumps(context.dict())
            }
            
            await self.redis_client.xadd(thinking_stream, startup_message)
            await self.redis_client.xadd(progress_stream, startup_message)
            
            # Set stream expiration (24 hours)
            await self.redis_client.expire(thinking_stream, 86400)
            await self.redis_client.expire(progress_stream, 86400)
            
            logger.info("✅ Created streaming session", 
                       session_id=session_id, user_id=user_id, debug_mode=config.debug_mode)
            
            return session
            
        except Exception as e:
            logger.error("❌ Failed to create streaming session", 
                        session_id=session_id, error=str(e))
            raise
    
    async def stream_thinking_step(self, thinking_step: ThinkingStep) -> bool:
        """Stream a thinking step to Redis"""
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return False
            
            session_id = thinking_step.session_id
            config = self.stream_configs.get(session_id)
            
            if not config:
                logger.warning("No stream config found for session", session_id=session_id)
                return False
            
            # Only stream thinking steps in debug mode
            if not config.debug_mode:
                return True
            
            stream_name = f"{config.thinking_stream_name}:{session_id}"
            
            # Convert thinking step to Redis message
            message_data = {
                "type": "thinking_step",
                "session_id": session_id,
                "timestamp": thinking_step.timestamp.isoformat(),
                "thinking_type": thinking_step.thinking_type.value,
                "content": thinking_step.content,
                "reasoning_chain": json.dumps(thinking_step.reasoning_chain),
                "confidence_level": str(thinking_step.confidence_level),
                "alternatives_considered": json.dumps(thinking_step.alternatives_considered),
                "decision_factors": json.dumps(thinking_step.decision_factors),
                "context_used": json.dumps(thinking_step.context_used) if thinking_step.context_used else "",
                "estimated_duration": str(thinking_step.estimated_duration) if thinking_step.estimated_duration else ""
            }
            
            # Add to Redis stream
            await self.redis_client.xadd(stream_name, message_data)
            
            # Trim stream to max length
            await self.redis_client.xtrim(stream_name, maxlen=config.max_stream_length, approximate=True)
            
            # Update session stats
            if session_id in self.active_sessions:
                self.active_sessions[session_id].thinking_steps_count += 1
                self.active_sessions[session_id].last_activity = datetime.now()
            
            logger.debug("📡 Streamed thinking step", 
                        session_id=session_id, thinking_type=thinking_step.thinking_type.value)
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to stream thinking step", 
                        session_id=thinking_step.session_id, error=str(e))
            return False
    
    async def stream_progress_update(self, progress_update: ProgressUpdate) -> bool:
        """Stream a progress update to Redis"""
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return False
            
            session_id = progress_update.session_id
            config = self.stream_configs.get(session_id)
            
            if not config:
                logger.warning("No stream config found for session", session_id=session_id)
                return False
            
            stream_name = f"{config.progress_stream_name}:{session_id}"
            
            # Convert progress update to Redis message
            message_data = {
                "type": "progress_update",
                "session_id": session_id,
                "timestamp": progress_update.timestamp.isoformat(),
                "update_type": progress_update.update_type.value,
                "message": progress_update.message,
                "progress_percentage": str(progress_update.progress_percentage) if progress_update.progress_percentage is not None else "",
                "current_step": progress_update.current_step or "",
                "total_steps": str(progress_update.total_steps) if progress_update.total_steps is not None else "",
                "estimated_remaining": progress_update.estimated_remaining or "",
                "intermediate_findings": json.dumps(progress_update.intermediate_findings) if progress_update.intermediate_findings else "",
                "current_activity": progress_update.current_activity or "",
                "confidence": str(progress_update.confidence) if progress_update.confidence is not None else ""
            }
            
            # Add to Redis stream
            await self.redis_client.xadd(stream_name, message_data)
            
            # Trim stream to max length
            await self.redis_client.xtrim(stream_name, maxlen=config.max_stream_length, approximate=True)
            
            # Update session stats
            if session_id in self.active_sessions:
                self.active_sessions[session_id].progress_updates_count += 1
                self.active_sessions[session_id].last_activity = datetime.now()
            
            logger.debug("📡 Streamed progress update", 
                        session_id=session_id, update_type=progress_update.update_type.value)
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to stream progress update", 
                        session_id=progress_update.session_id, error=str(e))
            return False
    
    async def read_thinking_stream(self, session_id: str, 
                                 last_id: str = "0", count: int = 100) -> List[Dict[str, Any]]:
        """Read thinking steps from Redis stream"""
        try:
            if not self.redis_client:
                return []
            
            config = self.stream_configs.get(session_id)
            if not config:
                return []
            
            stream_name = f"{config.thinking_stream_name}:{session_id}"
            
            # Read from stream
            messages = await self.redis_client.xread({stream_name: last_id}, count=count)
            
            result = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    # Parse the message
                    message = {
                        "id": msg_id,
                        "stream": stream,
                        **fields
                    }
                    
                    # Parse JSON fields
                    if "reasoning_chain" in message and message["reasoning_chain"]:
                        message["reasoning_chain"] = json.loads(message["reasoning_chain"])
                    if "alternatives_considered" in message and message["alternatives_considered"]:
                        message["alternatives_considered"] = json.loads(message["alternatives_considered"])
                    if "decision_factors" in message and message["decision_factors"]:
                        message["decision_factors"] = json.loads(message["decision_factors"])
                    if "context_used" in message and message["context_used"]:
                        message["context_used"] = json.loads(message["context_used"])
                    
                    result.append(message)
            
            return result
            
        except Exception as e:
            logger.error("❌ Failed to read thinking stream", 
                        session_id=session_id, error=str(e))
            return []
    
    async def read_progress_stream(self, session_id: str, 
                                 last_id: str = "0", count: int = 100) -> List[Dict[str, Any]]:
        """Read progress updates from Redis stream"""
        try:
            if not self.redis_client:
                return []
            
            config = self.stream_configs.get(session_id)
            if not config:
                return []
            
            stream_name = f"{config.progress_stream_name}:{session_id}"
            
            # Read from stream
            messages = await self.redis_client.xread({stream_name: last_id}, count=count)
            
            result = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    # Parse the message
                    message = {
                        "id": msg_id,
                        "stream": stream,
                        **fields
                    }
                    
                    # Parse JSON fields
                    if "intermediate_findings" in message and message["intermediate_findings"]:
                        message["intermediate_findings"] = json.loads(message["intermediate_findings"])
                    
                    result.append(message)
            
            return result
            
        except Exception as e:
            logger.error("❌ Failed to read progress stream", 
                        session_id=session_id, error=str(e))
            return []
    
    async def close_session(self, session_id: str) -> bool:
        """Close a streaming session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.is_active = False
                
                # Send session end message
                config = self.stream_configs.get(session_id)
                if config and self.redis_client:
                    end_message = {
                        "type": "session_end",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "duration": (datetime.now() - session.created_at).total_seconds(),
                        "thinking_steps": session.thinking_steps_count,
                        "progress_updates": session.progress_updates_count
                    }
                    
                    thinking_stream = f"{config.thinking_stream_name}:{session_id}"
                    progress_stream = f"{config.progress_stream_name}:{session_id}"
                    
                    await self.redis_client.xadd(thinking_stream, end_message)
                    await self.redis_client.xadd(progress_stream, end_message)
                
                # Clean up
                del self.active_sessions[session_id]
                if session_id in self.stream_configs:
                    del self.stream_configs[session_id]
                
                logger.info("✅ Closed streaming session", session_id=session_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("❌ Failed to close streaming session", 
                        session_id=session_id, error=str(e))
            return False
    
    async def get_session_stats(self, session_id: str) -> Optional[StreamStats]:
        """Get statistics for a streaming session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None
            
            duration = (datetime.now() - session.created_at).total_seconds()
            
            return StreamStats(
                session_id=session_id,
                total_thinking_steps=session.thinking_steps_count,
                total_progress_updates=session.progress_updates_count,
                session_duration=duration,
                last_updated=session.last_activity
            )
            
        except Exception as e:
            logger.error("❌ Failed to get session stats", 
                        session_id=session_id, error=str(e))
            return None
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old inactive sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, session in self.active_sessions.items():
                if session.last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                await self.close_session(session_id)
            
            logger.info("🧹 Cleaned up old sessions", count=len(sessions_to_remove))
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error("❌ Failed to cleanup old sessions", error=str(e))
            return 0
    
    async def shutdown(self):
        """Shutdown the stream manager"""
        try:
            # Close all active sessions
            for session_id in list(self.active_sessions.keys()):
                await self.close_session(session_id)
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("✅ Redis thinking stream manager shutdown complete")
            
        except Exception as e:
            logger.error("❌ Error during stream manager shutdown", error=str(e))
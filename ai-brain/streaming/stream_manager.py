"""
Central stream manager for coordinating all streaming operations
"""

import asyncio
import structlog
from typing import Optional, Dict, Any
from datetime import datetime

from .redis_thinking_stream import RedisThinkingStreamManager
from .thinking_data_models import (
    ThinkingStep, ProgressUpdate, StreamConfig, ThinkingContext,
    StreamingSession, ThinkingType, ProgressType
)

logger = structlog.get_logger()


class CentralStreamManager:
    """Central manager for all streaming operations"""
    
    def __init__(self, redis_url: str = "redis://opsconductor-redis:6379"):
        self.redis_stream_manager = RedisThinkingStreamManager(redis_url)
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the stream manager"""
        try:
            success = await self.redis_stream_manager.initialize()
            if success:
                self.is_initialized = True
                logger.info("✅ Central stream manager initialized")
                
                # Start cleanup task
                asyncio.create_task(self._periodic_cleanup())
                
            return success
            
        except Exception as e:
            logger.error("❌ Failed to initialize central stream manager", error=str(e))
            return False
    
    async def create_thinking_session(self, session_id: str, user_id: str,
                                    debug_mode: bool = False,
                                    user_request: str = "",
                                    system_context: Optional[Dict[str, Any]] = None) -> StreamingSession:
        """Create a new thinking session"""
        try:
            if not self.is_initialized:
                raise Exception("Stream manager not initialized")
            
            # Create stream configuration
            config = StreamConfig(
                session_id=session_id,
                debug_mode=debug_mode,
                progress_updates=True,
                thinking_stream_name="thinking",
                progress_stream_name="progress"
            )
            
            # Create thinking context
            context = ThinkingContext(
                user_request=user_request,
                system_context=system_context or {},
                conversation_history=[],
                available_services={},
                user_preferences={},
                safety_constraints=[]
            )
            
            # Create session
            session = await self.redis_stream_manager.create_session(
                session_id, user_id, config, context
            )
            
            logger.info("✅ Created thinking session", 
                       session_id=session_id, debug_mode=debug_mode)
            
            return session
            
        except Exception as e:
            logger.error("❌ Failed to create thinking session", 
                        session_id=session_id, error=str(e))
            raise
    
    async def stream_thinking(self, session_id: str, thinking_type: ThinkingType,
                            content: str, reasoning_chain: list = None,
                            confidence: float = 0.8, alternatives: list = None,
                            decision_factors: list = None,
                            context_used: Dict[str, Any] = None) -> bool:
        """Stream a thinking step"""
        try:
            if not self.is_initialized:
                return False
            
            thinking_step = ThinkingStep(
                session_id=session_id,
                thinking_type=thinking_type,
                content=content,
                reasoning_chain=reasoning_chain or [],
                confidence_level=confidence,
                alternatives_considered=alternatives or [],
                decision_factors=decision_factors or [],
                context_used=context_used
            )
            
            return await self.redis_stream_manager.stream_thinking_step(thinking_step)
            
        except Exception as e:
            logger.error("❌ Failed to stream thinking step", 
                        session_id=session_id, error=str(e))
            return False
    
    async def stream_progress(self, session_id: str, progress_type: ProgressType,
                            message: str, progress_percentage: float = None,
                            current_step: str = None, total_steps: int = None,
                            estimated_remaining: str = None,
                            intermediate_findings: list = None,
                            current_activity: str = None,
                            confidence: float = None) -> bool:
        """Stream a progress update"""
        try:
            if not self.is_initialized:
                return False
            
            progress_update = ProgressUpdate(
                session_id=session_id,
                update_type=progress_type,
                message=message,
                progress_percentage=progress_percentage,
                current_step=current_step,
                total_steps=total_steps,
                estimated_remaining=estimated_remaining,
                intermediate_findings=intermediate_findings,
                current_activity=current_activity,
                confidence=confidence
            )
            
            return await self.redis_stream_manager.stream_progress_update(progress_update)
            
        except Exception as e:
            logger.error("❌ Failed to stream progress update", 
                        session_id=session_id, error=str(e))
            return False
    
    async def close_session(self, session_id: str) -> bool:
        """Close a thinking session"""
        try:
            if not self.is_initialized:
                return False
            
            return await self.redis_stream_manager.close_session(session_id)
            
        except Exception as e:
            logger.error("❌ Failed to close session", 
                        session_id=session_id, error=str(e))
            return False
    
    async def get_session_stats(self, session_id: str):
        """Get session statistics"""
        try:
            if not self.is_initialized:
                return None
            
            return await self.redis_stream_manager.get_session_stats(session_id)
            
        except Exception as e:
            logger.error("❌ Failed to get session stats", 
                        session_id=session_id, error=str(e))
            return None
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.redis_stream_manager.cleanup_old_sessions(max_age_hours=24)
                
            except Exception as e:
                logger.error("❌ Error in periodic cleanup", error=str(e))
    
    async def shutdown(self):
        """Shutdown the stream manager"""
        try:
            await self.redis_stream_manager.shutdown()
            self.is_initialized = False
            logger.info("✅ Central stream manager shutdown complete")
            
        except Exception as e:
            logger.error("❌ Error during stream manager shutdown", error=str(e))


# Global stream manager instance
global_stream_manager: Optional[CentralStreamManager] = None


async def initialize_global_stream_manager(redis_url: str = "redis://opsconductor-redis:6379") -> bool:
    """Initialize the global stream manager"""
    global global_stream_manager
    
    try:
        global_stream_manager = CentralStreamManager(redis_url)
        success = await global_stream_manager.initialize()
        
        if success:
            logger.info("✅ Global stream manager initialized")
        else:
            logger.error("❌ Failed to initialize global stream manager")
            
        return success
        
    except Exception as e:
        logger.error("❌ Exception initializing global stream manager", error=str(e))
        return False


def get_global_stream_manager() -> Optional[CentralStreamManager]:
    """Get the global stream manager"""
    return global_stream_manager


# Convenience functions for easy access
async def create_session(session_id: str, user_id: str, debug_mode: bool = False,
                        user_request: str = "", system_context: Dict[str, Any] = None):
    """Create a thinking session"""
    manager = get_global_stream_manager()
    if manager:
        return await manager.create_thinking_session(
            session_id, user_id, debug_mode, user_request, system_context
        )
    return None


async def stream_thinking(session_id: str, thinking_type: str, content: str,
                         reasoning_chain: list = None, confidence: float = 0.8,
                         alternatives: list = None, decision_factors: list = None):
    """Stream a thinking step"""
    manager = get_global_stream_manager()
    if manager:
        thinking_type_enum = ThinkingType(thinking_type)
        return await manager.stream_thinking(
            session_id, thinking_type_enum, content, reasoning_chain,
            confidence, alternatives, decision_factors
        )
    return False


async def stream_progress(session_id: str, progress_type: str, message: str,
                         progress_percentage: float = None, current_step: str = None,
                         estimated_remaining: str = None):
    """Stream a progress update"""
    manager = get_global_stream_manager()
    if manager:
        progress_type_enum = ProgressType(progress_type)
        return await manager.stream_progress(
            session_id, progress_type_enum, message, progress_percentage,
            current_step, estimated_remaining=estimated_remaining
        )
    return False


async def close_session(session_id: str):
    """Close a thinking session"""
    manager = get_global_stream_manager()
    if manager:
        return await manager.close_session(session_id)
    return False


async def get_session_stats(session_id: str):
    """Get session statistics"""
    manager = get_global_stream_manager()
    if manager:
        return await manager.get_session_stats(session_id)
    return None
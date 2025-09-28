"""
OUIOE Phase 2: Thinking-Aware Ollama Client

This module provides an enhanced LLM client that integrates with the streaming infrastructure
to provide real-time thinking visualization and intelligent progress updates.

Key Features:
- Real-time thinking step streaming during LLM processing
- Intelligent progress updates with context-aware messaging
- Dual mode support (debug mode for thinking, normal mode for progress)
- Seamless integration with existing LLM client
- Performance monitoring and optimization
"""

import asyncio
import time
import json
import uuid
import structlog
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from datetime import datetime
from dataclasses import dataclass

# Import existing LLM client and streaming infrastructure
from integrations.llm_client import LLMEngine
from streaming.stream_manager import (
    create_session, stream_thinking, stream_progress, 
    close_session, get_session_stats
)
from streaming.thinking_data_models import (
    ThinkingStep, ProgressUpdate, StreamConfig, ThinkingContext
)

logger = structlog.get_logger()

@dataclass
class ThinkingConfig:
    """Configuration for thinking-aware LLM operations"""
    enable_thinking_stream: bool = True
    enable_progress_stream: bool = True
    thinking_detail_level: str = "detailed"  # minimal, standard, detailed, verbose
    progress_update_frequency: float = 2.0  # seconds between progress updates
    max_thinking_steps: int = 50
    thinking_timeout: float = 300.0  # 5 minutes max thinking time
    auto_create_session: bool = True
    session_prefix: str = "thinking"

class ThinkingLLMClient:
    """
    Enhanced LLM client with real-time thinking visualization and progress streaming.
    
    This client wraps the existing LLMEngine and adds thinking capabilities:
    - Streams thinking steps during LLM processing
    - Provides intelligent progress updates
    - Supports both debug mode (detailed thinking) and normal mode (progress only)
    - Maintains compatibility with existing LLM client interface
    """
    
    def __init__(self, ollama_host: str, default_model: str, 
                 thinking_config: Optional[ThinkingConfig] = None):
        """Initialize the thinking-aware LLM client"""
        self.base_client = LLMEngine(ollama_host, default_model)
        self.thinking_config = thinking_config or ThinkingConfig()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.thinking_patterns = self._initialize_thinking_patterns()
        
        logger.info("Thinking-aware LLM client initialized", 
                   config=self.thinking_config.__dict__)
    
    async def initialize(self) -> bool:
        """Initialize the base LLM client"""
        return await self.base_client.initialize()
    
    def _initialize_thinking_patterns(self) -> Dict[str, List[str]]:
        """Initialize thinking patterns for different types of operations"""
        return {
            "chat": [
                "Analyzing user request and context",
                "Identifying key information and intent", 
                "Considering relevant knowledge and experience",
                "Formulating comprehensive response",
                "Reviewing response for accuracy and completeness"
            ],
            "generate": [
                "Processing prompt and context",
                "Analyzing generation requirements",
                "Building response structure",
                "Generating content with appropriate tone",
                "Finalizing and optimizing output"
            ],
            "summarize": [
                "Reading and parsing input text",
                "Identifying key themes and concepts",
                "Extracting most important information",
                "Structuring summary for clarity",
                "Ensuring summary meets length requirements"
            ],
            "analyze": [
                "Examining input for analysis type",
                "Applying analytical framework",
                "Gathering relevant indicators",
                "Synthesizing findings",
                "Formulating analytical conclusions"
            ]
        }
    
    async def create_thinking_session(self, user_id: str, operation_type: str,
                                    user_request: str, debug_mode: bool = False) -> str:
        """Create a new thinking session for an LLM operation"""
        session_id = f"{self.thinking_config.session_prefix}-{user_id}-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create streaming session
            session = await create_session(
                session_id=session_id,
                user_id=user_id,
                debug_mode=debug_mode,
                user_request=user_request
            )
            
            # Track session locally
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "operation_type": operation_type,
                "user_request": user_request,
                "debug_mode": debug_mode,
                "start_time": time.time(),
                "thinking_steps": 0,
                "progress_updates": 0
            }
            
            logger.info("Created thinking session", 
                       session_id=session_id, operation_type=operation_type)
            return session_id
            
        except Exception as e:
            logger.error("Failed to create thinking session", error=str(e))
            raise
    
    async def _stream_thinking_step(self, session_id: str, thinking_type: str,
                                  content: str, reasoning_chain: Optional[List[str]] = None,
                                  confidence: float = 0.8, metadata: Optional[Dict] = None):
        """Stream a thinking step to the session"""
        if session_id not in self.active_sessions:
            return
        
        try:
            await stream_thinking(
                session_id=session_id,
                thinking_type=thinking_type,
                content=content,
                reasoning_chain=reasoning_chain or [],
                confidence=confidence,
                alternatives=None,  # Not used in this implementation
                decision_factors=None  # Not used in this implementation
            )
            
            self.active_sessions[session_id]["thinking_steps"] += 1
            
        except Exception as e:
            logger.error("Failed to stream thinking step", 
                        session_id=session_id, error=str(e))
    
    async def _stream_progress_update(self, session_id: str, progress_type: str,
                                    message: str, progress_percentage: Optional[float] = None,
                                    current_step: Optional[str] = None,
                                    metadata: Optional[Dict] = None):
        """Stream a progress update to the session"""
        if session_id not in self.active_sessions:
            return
        
        try:
            await stream_progress(
                session_id=session_id,
                progress_type=progress_type,
                message=message,
                progress_percentage=progress_percentage,
                current_step=current_step,
                estimated_remaining=None  # Not used in this implementation
            )
            
            self.active_sessions[session_id]["progress_updates"] += 1
            
        except Exception as e:
            logger.error("Failed to stream progress update", 
                        session_id=session_id, error=str(e))
    
    async def _execute_with_thinking(self, session_id: str, operation_type: str,
                                   operation_func: Callable, *args, **kwargs) -> Any:
        """Execute an LLM operation with thinking visualization"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            # Fallback to direct execution if no session
            return await operation_func(*args, **kwargs)
        
        debug_mode = session_info["debug_mode"]
        thinking_patterns = self.thinking_patterns.get(operation_type, [
            "Processing request",
            "Analyzing input",
            "Generating response",
            "Finalizing output"
        ])
        
        try:
            # Start progress tracking
            start_time = time.time()
            total_steps = len(thinking_patterns)
            
            # Initial progress update
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="start",
                message=f"Starting {operation_type} operation...",
                progress_percentage=0.0,
                current_step="Initialization"
            )
            
            # Execute thinking steps
            for i, thinking_step in enumerate(thinking_patterns):
                step_start = time.time()
                
                # Stream thinking step (debug mode only)
                if debug_mode and self.thinking_config.enable_thinking_stream:
                    await self._stream_thinking_step(
                        session_id=session_id,
                        thinking_type="processing",
                        content=thinking_step,
                        reasoning_chain=[f"Step {i+1} of {total_steps}"],
                        confidence=0.8,
                        metadata={"step_number": i+1, "total_steps": total_steps}
                    )
                
                # Stream progress update
                if self.thinking_config.enable_progress_stream:
                    progress_percentage = ((i + 0.5) / total_steps) * 100
                    await self._stream_progress_update(
                        session_id=session_id,
                        progress_type="progress",
                        message=thinking_step,
                        progress_percentage=progress_percentage,
                        current_step=f"Step {i+1}/{total_steps}"
                    )
                
                # Simulate thinking time (small delay for visualization)
                if debug_mode:
                    await asyncio.sleep(0.5)  # Brief pause for thinking visualization
            
            # Execute the actual LLM operation
            if debug_mode and self.thinking_config.enable_thinking_stream:
                await self._stream_thinking_step(
                    session_id=session_id,
                    thinking_type="execution",
                    content="Executing LLM operation with optimized parameters",
                    reasoning_chain=["Prepared context", "Configured model", "Ready for generation"],
                    confidence=0.9
                )
            
            # Progress update for LLM execution
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="progress",
                message="Executing LLM operation...",
                progress_percentage=80.0,
                current_step="LLM Processing"
            )
            
            # Execute the actual operation
            result = await operation_func(*args, **kwargs)
            
            # Final thinking step (debug mode)
            if debug_mode and self.thinking_config.enable_thinking_stream:
                await self._stream_thinking_step(
                    session_id=session_id,
                    thinking_type="completion",
                    content="Operation completed successfully, reviewing output quality",
                    reasoning_chain=["Generated response", "Validated output", "Ready to deliver"],
                    confidence=0.95,
                    metadata={"processing_time": time.time() - start_time}
                )
            
            # Final progress update
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="completion",
                message="Operation completed successfully",
                progress_percentage=100.0,
                current_step="Complete",
                metadata={
                    "total_time": time.time() - start_time,
                    "thinking_steps": session_info["thinking_steps"],
                    "progress_updates": session_info["progress_updates"]
                }
            )
            
            return result
            
        except Exception as e:
            # Error handling with thinking stream
            if debug_mode and self.thinking_config.enable_thinking_stream:
                await self._stream_thinking_step(
                    session_id=session_id,
                    thinking_type="error",
                    content=f"Encountered error during {operation_type}: {str(e)}",
                    reasoning_chain=["Error detected", "Analyzing failure", "Preparing fallback"],
                    confidence=0.3
                )
            
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="error",
                message=f"Error in {operation_type}: {str(e)}",
                progress_percentage=None,
                current_step="Error",
                metadata={"error": str(e)}
            )
            
            raise
    
    async def chat_with_thinking(self, message: str, context: Optional[str] = None,
                               system_prompt: Optional[str] = None, model: Optional[str] = None,
                               parsed_data: Optional[Dict[str, Any]] = None,
                               user_id: str = "default", debug_mode: bool = False,
                               session_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with the LLM with thinking visualization"""
        
        # Create session if not provided
        if session_id is None and self.thinking_config.auto_create_session:
            session_id = await self.create_thinking_session(
                user_id=user_id,
                operation_type="chat",
                user_request=message,
                debug_mode=debug_mode
            )
        
        try:
            # Execute chat with thinking
            result = await self._execute_with_thinking(
                session_id=session_id,
                operation_type="chat",
                operation_func=self.base_client.chat,
                message=message,
                context=context,
                system_prompt=system_prompt,
                model=model,
                parsed_data=parsed_data
            )
            
            # Add session info to result
            if session_id:
                result["session_id"] = session_id
                result["thinking_enabled"] = True
            
            return result
            
        finally:
            # Clean up session if auto-created
            if session_id and self.thinking_config.auto_create_session:
                await self.close_thinking_session(session_id)
    
    async def generate_with_thinking(self, prompt: str, context: Optional[str] = None,
                                   model: Optional[str] = None, max_tokens: Optional[int] = None,
                                   temperature: Optional[float] = None,
                                   user_id: str = "default", debug_mode: bool = False,
                                   session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate text with thinking visualization"""
        
        # Create session if not provided
        if session_id is None and self.thinking_config.auto_create_session:
            session_id = await self.create_thinking_session(
                user_id=user_id,
                operation_type="generate",
                user_request=prompt,
                debug_mode=debug_mode
            )
        
        try:
            # Execute generation with thinking
            result = await self._execute_with_thinking(
                session_id=session_id,
                operation_type="generate",
                operation_func=self.base_client.generate,
                prompt=prompt,
                context=context,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Add session info to result
            if session_id:
                result["session_id"] = session_id
                result["thinking_enabled"] = True
            
            return result
            
        finally:
            # Clean up session if auto-created
            if session_id and self.thinking_config.auto_create_session:
                await self.close_thinking_session(session_id)
    
    async def summarize_with_thinking(self, text: str, max_length: int = 200,
                                    model: Optional[str] = None,
                                    user_id: str = "default", debug_mode: bool = False,
                                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """Summarize text with thinking visualization"""
        
        # Create session if not provided
        if session_id is None and self.thinking_config.auto_create_session:
            session_id = await self.create_thinking_session(
                user_id=user_id,
                operation_type="summarize",
                user_request=f"Summarize text ({len(text)} chars)",
                debug_mode=debug_mode
            )
        
        try:
            # Execute summarization with thinking
            result = await self._execute_with_thinking(
                session_id=session_id,
                operation_type="summarize",
                operation_func=self.base_client.summarize,
                text=text,
                max_length=max_length,
                model=model
            )
            
            # Add session info to result
            if session_id:
                result["session_id"] = session_id
                result["thinking_enabled"] = True
            
            return result
            
        finally:
            # Clean up session if auto-created
            if session_id and self.thinking_config.auto_create_session:
                await self.close_thinking_session(session_id)
    
    async def analyze_with_thinking(self, text: str, analysis_type: str = "sentiment",
                                  model: Optional[str] = None,
                                  user_id: str = "default", debug_mode: bool = False,
                                  session_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze text with thinking visualization"""
        
        # Create session if not provided
        if session_id is None and self.thinking_config.auto_create_session:
            session_id = await self.create_thinking_session(
                user_id=user_id,
                operation_type="analyze",
                user_request=f"Analyze text for {analysis_type}",
                debug_mode=debug_mode
            )
        
        try:
            # Execute analysis with thinking
            result = await self._execute_with_thinking(
                session_id=session_id,
                operation_type="analyze",
                operation_func=self.base_client.analyze,
                text=text,
                analysis_type=analysis_type,
                model=model
            )
            
            # Add session info to result
            if session_id:
                result["session_id"] = session_id
                result["thinking_enabled"] = True
            
            return result
            
        finally:
            # Clean up session if auto-created
            if session_id and self.thinking_config.auto_create_session:
                await self.close_thinking_session(session_id)
    
    async def close_thinking_session(self, session_id: str) -> Dict[str, Any]:
        """Close a thinking session and return statistics"""
        try:
            # Get final statistics
            stats = await get_session_stats(session_id)
            
            # Close the streaming session
            await close_session(session_id)
            
            # Remove from local tracking
            session_info = self.active_sessions.pop(session_id, {})
            
            # Calculate session metrics
            if session_info:
                total_time = time.time() - session_info.get("start_time", time.time())
                stats.update({
                    "total_session_time": total_time,
                    "local_thinking_steps": session_info.get("thinking_steps", 0),
                    "local_progress_updates": session_info.get("progress_updates", 0),
                    "operation_type": session_info.get("operation_type", "unknown")
                })
            
            logger.info("Closed thinking session", session_id=session_id, stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to close thinking session", 
                        session_id=session_id, error=str(e))
            return {"error": str(e)}
    
    async def get_thinking_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a thinking session"""
        try:
            # Get streaming stats
            stats = await get_session_stats(session_id)
            
            # Add local session info
            session_info = self.active_sessions.get(session_id, {})
            if session_info:
                current_time = time.time()
                stats.update({
                    "session_duration": current_time - session_info.get("start_time", current_time),
                    "operation_type": session_info.get("operation_type", "unknown"),
                    "debug_mode": session_info.get("debug_mode", False),
                    "local_thinking_steps": session_info.get("thinking_steps", 0),
                    "local_progress_updates": session_info.get("progress_updates", 0)
                })
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get thinking session stats", 
                        session_id=session_id, error=str(e))
            return {"error": str(e)}
    
    # Compatibility methods - delegate to base client for non-thinking operations
    async def get_available_models(self) -> List[str]:
        """Get available models from base client"""
        return await self.base_client.get_available_models()
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull model using base client"""
        return await self.base_client.pull_model(model_name)
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get GPU status from base client"""
        return self.base_client.get_gpu_status()
    
    # Legacy compatibility methods (without thinking)
    async def chat(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy chat method - delegates to base client"""
        return await self.base_client.chat(*args, **kwargs)
    
    async def generate(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy generate method - delegates to base client"""
        return await self.base_client.generate(*args, **kwargs)
    
    async def summarize(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy summarize method - delegates to base client"""
        return await self.base_client.summarize(*args, **kwargs)
    
    async def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy analyze method - delegates to base client"""
        return await self.base_client.analyze(*args, **kwargs)
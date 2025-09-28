"""
OUIOE Phase 3: Intelligent Thinking-Aware Ollama Client

This module provides an enhanced LLM client that integrates with the streaming infrastructure
and intelligence systems to provide real-time thinking visualization, intelligent progress 
updates, and contextual progress communication.

Key Features:
- Real-time thinking step streaming during LLM processing
- Intelligent progress updates with context-aware messaging
- Dynamic milestone detection and complexity assessment
- Adaptive progress communication based on operation context
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

# Import Phase 3 intelligence systems
from intelligence import (
    ProgressIntelligenceEngine,
    OperationAnalyzer,
    SmartProgressMessaging,
    OperationType,
    ComplexityLevel,
    ProgressPhase,
    MessageContext,
    MessageTone,
    create_progress_intelligence_engine,
    create_operation_analyzer,
    create_smart_progress_messaging
)

logger = structlog.get_logger()

@dataclass
class ThinkingConfig:
    """Configuration for thinking-aware LLM operations with intelligence"""
    enable_thinking_stream: bool = True
    enable_progress_stream: bool = True
    enable_intelligence: bool = True  # Enable Phase 3 intelligence features
    thinking_detail_level: str = "detailed"  # minimal, standard, detailed, verbose
    progress_update_frequency: float = 2.0  # seconds between progress updates
    max_thinking_steps: int = 50
    thinking_timeout: float = 300.0  # 5 minutes max thinking time
    auto_create_session: bool = True
    session_prefix: str = "thinking"
    
    # Phase 3 Intelligence Configuration
    enable_contextual_messaging: bool = True
    enable_dynamic_milestones: bool = True
    enable_complexity_analysis: bool = True
    enable_adaptive_communication: bool = True
    message_tone: MessageTone = MessageTone.FRIENDLY
    operation_analysis_depth: str = "standard"  # minimal, standard, comprehensive

class ThinkingLLMClient:
    """
    Enhanced LLM client with real-time thinking visualization, intelligent progress 
    streaming, and contextual progress communication.
    
    This client wraps the existing LLMEngine and adds thinking capabilities:
    - Streams thinking steps during LLM processing
    - Provides intelligent progress updates with context awareness
    - Dynamic milestone detection and complexity assessment
    - Adaptive progress communication based on operation context
    - Supports both debug mode (detailed thinking) and normal mode (progress only)
    - Maintains compatibility with existing LLM client interface
    """
    
    def __init__(self, ollama_host: str, default_model: str, 
                 thinking_config: Optional[ThinkingConfig] = None):
        """Initialize the intelligent thinking-aware LLM client"""
        self.base_client = LLMEngine(ollama_host, default_model)
        self.thinking_config = thinking_config or ThinkingConfig()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.thinking_patterns = self._initialize_thinking_patterns()
        
        # Initialize Phase 3 intelligence systems
        if self.thinking_config.enable_intelligence:
            self.progress_intelligence = create_progress_intelligence_engine()
            self.operation_analyzer = create_operation_analyzer()
            self.smart_messaging = create_smart_progress_messaging()
            logger.info("Intelligence systems initialized for thinking client")
        else:
            self.progress_intelligence = None
            self.operation_analyzer = None
            self.smart_messaging = None
        
        logger.info("Intelligent thinking-aware LLM client initialized", 
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
        """Execute an LLM operation with intelligent thinking visualization"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            # Fallback to direct execution if no session
            return await operation_func(*args, **kwargs)
        
        debug_mode = session_info["debug_mode"]
        user_request = session_info.get("user_request", "")
        user_id = session_info.get("user_id", "default")
        
        # Phase 3: Initialize intelligence analysis
        operation_context = None
        operation_metrics = None
        progress_intelligence = None
        dynamic_milestones = []
        
        if self.thinking_config.enable_intelligence and self.progress_intelligence:
            try:
                # Analyze operation context
                operation_context = await self.progress_intelligence.analyze_operation(
                    message=user_request,
                    context={"operation_type": operation_type, "debug_mode": debug_mode}
                )
                
                # Generate dynamic milestones
                if self.thinking_config.enable_dynamic_milestones:
                    dynamic_milestones = await self.progress_intelligence.generate_dynamic_milestones(
                        operation_context
                    )
                
                logger.info("Operation intelligence analysis complete",
                           operation_type=operation_context.operation_type.value,
                           complexity=operation_context.complexity_level.value,
                           milestones=len(dynamic_milestones))
                
            except Exception as e:
                logger.warning("Intelligence analysis failed, falling back to standard patterns", error=str(e))
        
        # Use intelligent milestones or fallback to standard patterns
        if dynamic_milestones:
            thinking_patterns = [milestone.description for milestone in dynamic_milestones]
        else:
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
            
            # Generate intelligent initial message
            initial_message = f"Starting {operation_type} operation..."
            if (self.thinking_config.enable_contextual_messaging and 
                self.smart_messaging and operation_context):
                try:
                    adaptive_msg = await self.smart_messaging.generate_adaptive_message(
                        progress_intelligence=None,  # Will be created later
                        operation_metrics=None,      # Will be created later
                        message_context=MessageContext.STARTUP,
                        user_id=user_id
                    )
                    initial_message = adaptive_msg.content
                except Exception as e:
                    logger.warning("Failed to generate adaptive startup message", error=str(e))
            
            # Initial progress update
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="start",
                message=initial_message,
                progress_percentage=0.0,
                current_step="Initialization"
            )
            
            # Execute thinking steps with intelligence
            thinking_steps_content = []
            for i, thinking_step in enumerate(thinking_patterns):
                step_start = time.time()
                elapsed_time = time.time() - start_time
                
                # Phase 3: Generate intelligent progress analysis
                if (self.thinking_config.enable_intelligence and 
                    operation_context and self.progress_intelligence):
                    try:
                        # Analyze operation metrics
                        if self.thinking_config.enable_complexity_analysis and self.operation_analyzer:
                            operation_metrics = await self.operation_analyzer.analyze_operation_depth(
                                message=user_request,
                                operation_context=operation_context,
                                thinking_steps=thinking_steps_content
                            )
                        
                        # Calculate progress intelligence
                        progress_intelligence = await self.progress_intelligence.calculate_progress_intelligence(
                            operation_context=operation_context,
                            milestones=dynamic_milestones,
                            current_step=i + 1,
                            total_steps=total_steps,
                            elapsed_time=elapsed_time
                        )
                        
                        # Generate adaptive progress message
                        if self.thinking_config.enable_adaptive_communication and self.smart_messaging:
                            adaptive_msg = await self.smart_messaging.generate_adaptive_message(
                                progress_intelligence=progress_intelligence,
                                operation_metrics=operation_metrics or type('obj', (object,), {'complexity_indicators': []})(),
                                message_context=MessageContext.PROGRESS,
                                user_id=user_id,
                                elapsed_time=elapsed_time
                            )
                            intelligent_message = adaptive_msg.content
                            
                            # Check for milestone reached
                            if progress_intelligence.next_milestone:
                                milestone_progress = progress_intelligence.completion_percentage
                                milestone_threshold = progress_intelligence.next_milestone.estimated_completion
                                
                                if milestone_progress >= milestone_threshold - 0.1:  # Close to milestone
                                    milestone_msg = await self.smart_messaging.generate_adaptive_message(
                                        progress_intelligence=progress_intelligence,
                                        operation_metrics=operation_metrics or type('obj', (object,), {'complexity_indicators': []})(),
                                        message_context=MessageContext.MILESTONE,
                                        user_id=user_id,
                                        elapsed_time=elapsed_time
                                    )
                                    intelligent_message = milestone_msg.content
                        else:
                            intelligent_message = thinking_step
                            
                    except Exception as e:
                        logger.warning("Intelligence processing failed for step", step=i, error=str(e))
                        intelligent_message = thinking_step
                        progress_intelligence = None
                else:
                    intelligent_message = thinking_step
                    progress_intelligence = None
                
                # Store thinking step content for analysis
                thinking_steps_content.append(thinking_step)
                
                # Stream thinking step (debug mode only)
                if debug_mode and self.thinking_config.enable_thinking_stream:
                    await self._stream_thinking_step(
                        session_id=session_id,
                        thinking_type="processing",
                        content=thinking_step,
                        reasoning_chain=[f"Step {i+1} of {total_steps}"],
                        confidence=progress_intelligence.confidence_score if progress_intelligence else 0.8,
                        metadata={
                            "step_number": i+1, 
                            "total_steps": total_steps,
                            "intelligence_enabled": self.thinking_config.enable_intelligence,
                            "complexity": operation_context.complexity_level.value if operation_context else "unknown"
                        }
                    )
                
                # Stream intelligent progress update
                if self.thinking_config.enable_progress_stream:
                    if progress_intelligence:
                        progress_percentage = progress_intelligence.completion_percentage * 100
                        eta_info = f" (ETA: {progress_intelligence.eta_seconds:.1f}s)" if progress_intelligence.eta_seconds > 0 else ""
                        current_step_info = f"{progress_intelligence.current_phase.value.replace('_', ' ').title()}"
                    else:
                        progress_percentage = ((i + 0.5) / total_steps) * 100
                        eta_info = ""
                        current_step_info = f"Step {i+1}/{total_steps}"
                    
                    await self._stream_progress_update(
                        session_id=session_id,
                        progress_type="progress",
                        message=intelligent_message + eta_info,
                        progress_percentage=progress_percentage,
                        current_step=current_step_info
                    )
                
                # Simulate thinking time (small delay for visualization)
                if debug_mode:
                    # Intelligent delay based on complexity
                    if operation_context and operation_context.complexity_level == ComplexityLevel.ADVANCED:
                        await asyncio.sleep(0.8)  # Longer pause for complex operations
                    elif operation_context and operation_context.complexity_level == ComplexityLevel.SIMPLE:
                        await asyncio.sleep(0.3)  # Shorter pause for simple operations
                    else:
                        await asyncio.sleep(0.5)  # Standard pause
            
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
            
            # Phase 3: Generate intelligent completion analysis
            total_time = time.time() - start_time
            completion_message = "Operation completed successfully"
            
            if (self.thinking_config.enable_intelligence and 
                operation_context and self.smart_messaging):
                try:
                    # Final operation metrics analysis
                    if self.thinking_config.enable_complexity_analysis and self.operation_analyzer:
                        final_metrics = await self.operation_analyzer.analyze_operation_depth(
                            message=user_request,
                            operation_context=operation_context,
                            thinking_steps=thinking_steps_content
                        )
                        final_metrics.processing_time = total_time
                        
                        # Update operation history for learning
                        self.operation_analyzer.update_operation_history(
                            operation_context.operation_type, final_metrics
                        )
                    
                    # Generate intelligent completion message
                    if self.thinking_config.enable_adaptive_communication:
                        final_progress_intelligence = await self.progress_intelligence.calculate_progress_intelligence(
                            operation_context=operation_context,
                            milestones=dynamic_milestones,
                            current_step=total_steps,
                            total_steps=total_steps,
                            elapsed_time=total_time
                        )
                        
                        completion_msg = await self.smart_messaging.generate_adaptive_message(
                            progress_intelligence=final_progress_intelligence,
                            operation_metrics=final_metrics if 'final_metrics' in locals() else None,
                            message_context=MessageContext.COMPLETION,
                            user_id=user_id,
                            elapsed_time=total_time
                        )
                        completion_message = completion_msg.content
                        
                        # Record user interaction for learning
                        self.smart_messaging.record_user_interaction(user_id, completion_message)
                        
                except Exception as e:
                    logger.warning("Intelligence completion analysis failed", error=str(e))
            
            # Final thinking step (debug mode)
            if debug_mode and self.thinking_config.enable_thinking_stream:
                await self._stream_thinking_step(
                    session_id=session_id,
                    thinking_type="completion",
                    content="Operation completed successfully, reviewing output quality",
                    reasoning_chain=["Generated response", "Validated output", "Ready to deliver"],
                    confidence=0.95,
                    metadata={
                        "processing_time": total_time,
                        "intelligence_enabled": self.thinking_config.enable_intelligence,
                        "operation_type": operation_context.operation_type.value if operation_context else operation_type,
                        "complexity": operation_context.complexity_level.value if operation_context else "unknown"
                    }
                )
            
            # Final progress update with intelligence
            await self._stream_progress_update(
                session_id=session_id,
                progress_type="completion",
                message=completion_message,
                progress_percentage=100.0,
                current_step="Complete",
                metadata={
                    "total_time": total_time,
                    "thinking_steps": session_info["thinking_steps"],
                    "progress_updates": session_info["progress_updates"],
                    "intelligence_enabled": self.thinking_config.enable_intelligence,
                    "operation_type": operation_context.operation_type.value if operation_context else operation_type,
                    "complexity_level": operation_context.complexity_level.value if operation_context else "unknown",
                    "milestones_used": len(dynamic_milestones) if dynamic_milestones else 0
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
    
    # Phase 3: Intelligence Methods
    
    def get_intelligence_capabilities(self) -> Dict[str, Any]:
        """Get intelligence capabilities and configuration"""
        return {
            "intelligence_enabled": self.thinking_config.enable_intelligence,
            "contextual_messaging": self.thinking_config.enable_contextual_messaging,
            "dynamic_milestones": self.thinking_config.enable_dynamic_milestones,
            "complexity_analysis": self.thinking_config.enable_complexity_analysis,
            "adaptive_communication": self.thinking_config.enable_adaptive_communication,
            "message_tone": self.thinking_config.message_tone.value if hasattr(self.thinking_config.message_tone, 'value') else str(self.thinking_config.message_tone),
            "operation_analysis_depth": self.thinking_config.operation_analysis_depth,
            "intelligence_systems": {
                "progress_intelligence": self.progress_intelligence is not None,
                "operation_analyzer": self.operation_analyzer is not None,
                "smart_messaging": self.smart_messaging is not None
            }
        }
    
    async def set_user_message_tone(self, user_id: str, tone: MessageTone):
        """Set user's preferred message tone"""
        if self.smart_messaging:
            self.smart_messaging.set_user_tone_preference(user_id, tone)
            logger.info("Updated user message tone preference", user_id=user_id, tone=tone.value)
    
    async def get_operation_insights(self, operation_type: str) -> Dict[str, Any]:
        """Get insights about operation patterns"""
        if not self.operation_analyzer:
            return {"error": "Operation analyzer not available"}
        
        try:
            # Convert string to OperationType enum
            op_type = OperationType(operation_type.lower())
            insights = self.operation_analyzer.get_operation_insights(op_type)
            return insights
        except ValueError:
            return {"error": f"Unknown operation type: {operation_type}"}
        except Exception as e:
            logger.error("Failed to get operation insights", error=str(e))
            return {"error": str(e)}
    
    async def get_messaging_insights(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get insights about messaging patterns"""
        if not self.smart_messaging:
            return {"error": "Smart messaging not available"}
        
        try:
            insights = self.smart_messaging.get_messaging_insights(user_id)
            return insights
        except Exception as e:
            logger.error("Failed to get messaging insights", error=str(e))
            return {"error": str(e)}
    
    async def analyze_message_complexity(self, message: str) -> Dict[str, Any]:
        """Analyze the complexity of a message without executing it"""
        if not self.progress_intelligence:
            return {"error": "Progress intelligence not available"}
        
        try:
            operation_context = await self.progress_intelligence.analyze_operation(message)
            
            return {
                "operation_type": operation_context.operation_type.value,
                "complexity_level": operation_context.complexity_level.value,
                "estimated_duration": operation_context.estimated_duration,
                "key_concepts": operation_context.key_concepts,
                "user_intent": operation_context.user_intent,
                "technical_domain": operation_context.technical_domain,
                "requirements": {
                    "requires_code": operation_context.requires_code,
                    "requires_analysis": operation_context.requires_analysis,
                    "requires_creativity": operation_context.requires_creativity
                }
            }
        except Exception as e:
            logger.error("Failed to analyze message complexity", error=str(e))
            return {"error": str(e)}
    
    async def predict_operation_trajectory(self, message: str) -> Dict[str, Any]:
        """Predict the trajectory of an operation without executing it"""
        if not self.progress_intelligence or not self.operation_analyzer:
            return {"error": "Intelligence systems not available"}
        
        try:
            # Analyze operation context
            operation_context = await self.progress_intelligence.analyze_operation(message)
            
            # Create mock metrics for prediction
            mock_metrics = type('MockMetrics', (), {
                'thinking_steps_count': 0,
                'complexity_indicators': [],
                'performance_score': 0.7,
                'context_switches': 0
            })()
            
            # Predict trajectory
            trajectory = await self.operation_analyzer.predict_operation_trajectory(
                operation_context, mock_metrics, 0.0
            )
            
            return {
                "operation_context": {
                    "type": operation_context.operation_type.value,
                    "complexity": operation_context.complexity_level.value,
                    "estimated_duration": operation_context.estimated_duration
                },
                "trajectory_prediction": trajectory
            }
        except Exception as e:
            logger.error("Failed to predict operation trajectory", error=str(e))
            return {"error": str(e)}
    
    def configure_intelligence(self, **config_updates):
        """Update intelligence configuration"""
        for key, value in config_updates.items():
            if hasattr(self.thinking_config, key):
                setattr(self.thinking_config, key, value)
                logger.info("Updated intelligence configuration", key=key, value=value)
            else:
                logger.warning("Unknown intelligence configuration key", key=key)
    
    def get_intelligence_status(self) -> Dict[str, Any]:
        """Get current intelligence system status"""
        return {
            "intelligence_enabled": self.thinking_config.enable_intelligence,
            "systems_initialized": {
                "progress_intelligence": self.progress_intelligence is not None,
                "operation_analyzer": self.operation_analyzer is not None,
                "smart_messaging": self.smart_messaging is not None
            },
            "active_sessions": len(self.active_sessions),
            "configuration": {
                "contextual_messaging": self.thinking_config.enable_contextual_messaging,
                "dynamic_milestones": self.thinking_config.enable_dynamic_milestones,
                "complexity_analysis": self.thinking_config.enable_complexity_analysis,
                "adaptive_communication": self.thinking_config.enable_adaptive_communication,
                "message_tone": self.thinking_config.message_tone.value if hasattr(self.thinking_config.message_tone, 'value') else str(self.thinking_config.message_tone)
            }
        }
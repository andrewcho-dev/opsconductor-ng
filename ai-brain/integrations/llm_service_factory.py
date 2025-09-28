"""
LLM Service Factory - OUIOE Phase 2

This module provides a factory for creating LLM clients with optional thinking capabilities.
It allows seamless switching between standard and thinking-aware LLM clients based on
configuration and user preferences.

Key Features:
- Factory pattern for LLM client creation
- Environment-based configuration
- Backward compatibility with existing code
- Easy integration with thinking capabilities
- Performance monitoring and optimization
"""

import os
import structlog
from typing import Optional, Dict, Any, Union
from enum import Enum

from integrations.llm_client import LLMEngine
from integrations.thinking_llm_client import ThinkingLLMClient, ThinkingConfig

logger = structlog.get_logger()

class LLMClientType(Enum):
    """Types of LLM clients available"""
    STANDARD = "standard"
    THINKING = "thinking"
    AUTO = "auto"  # Choose based on environment/config

class LLMServiceFactory:
    """
    Factory for creating LLM clients with optional thinking capabilities.
    
    This factory provides a unified interface for creating LLM clients,
    allowing applications to easily switch between standard and thinking-aware
    clients based on configuration or runtime requirements.
    """
    
    @staticmethod
    def create_client(client_type: Union[LLMClientType, str] = LLMClientType.AUTO,
                     ollama_host: Optional[str] = None,
                     default_model: Optional[str] = None,
                     thinking_config: Optional[ThinkingConfig] = None,
                     **kwargs) -> Union[LLMEngine, ThinkingLLMClient]:
        """
        Create an LLM client based on the specified type and configuration.
        
        Args:
            client_type: Type of client to create (standard, thinking, or auto)
            ollama_host: Ollama server host URL
            default_model: Default model to use
            thinking_config: Configuration for thinking capabilities
            **kwargs: Additional configuration options
            
        Returns:
            LLM client instance (either standard or thinking-aware)
        """
        
        # Normalize client type
        if isinstance(client_type, str):
            try:
                client_type = LLMClientType(client_type.lower())
            except ValueError:
                logger.warning(f"Unknown client type '{client_type}', using AUTO")
                client_type = LLMClientType.AUTO
        
        # Get configuration from environment if not provided
        ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://ollama:11434")
        default_model = default_model or os.getenv("DEFAULT_MODEL", "codellama:7b")
        
        # Auto-detect client type if needed
        if client_type == LLMClientType.AUTO:
            client_type = LLMServiceFactory._auto_detect_client_type()
        
        # Create thinking configuration if not provided
        if client_type == LLMClientType.THINKING and thinking_config is None:
            thinking_config = LLMServiceFactory._create_default_thinking_config()
        
        # Create the appropriate client
        if client_type == LLMClientType.THINKING:
            logger.info("Creating thinking-aware LLM client", 
                       host=ollama_host, model=default_model)
            return ThinkingLLMClient(
                ollama_host=ollama_host,
                default_model=default_model,
                thinking_config=thinking_config
            )
        else:
            logger.info("Creating standard LLM client", 
                       host=ollama_host, model=default_model)
            return LLMEngine(
                ollama_host=ollama_host,
                default_model=default_model
            )
    
    @staticmethod
    def _auto_detect_client_type() -> LLMClientType:
        """
        Auto-detect which client type to use based on environment configuration.
        
        Returns:
            LLMClientType: The detected client type
        """
        
        # Check environment variables for thinking mode preference
        thinking_enabled = os.getenv("ENABLE_THINKING_MODE", "false").lower()
        if thinking_enabled in ("true", "1", "yes", "on"):
            return LLMClientType.THINKING
        
        # Check for debug mode
        debug_mode = os.getenv("DEBUG", "false").lower()
        if debug_mode in ("true", "1", "yes", "on"):
            return LLMClientType.THINKING
        
        # Check for development environment
        environment = os.getenv("ENVIRONMENT", "production").lower()
        if environment in ("development", "dev", "local"):
            return LLMClientType.THINKING
        
        # Check if Redis is available (required for thinking mode)
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.info("Redis not configured, using standard LLM client")
            return LLMClientType.STANDARD
        
        # Default to thinking mode for better user experience
        return LLMClientType.THINKING
    
    @staticmethod
    def _create_default_thinking_config() -> ThinkingConfig:
        """
        Create default thinking configuration based on environment.
        
        Returns:
            ThinkingConfig: Default configuration
        """
        
        # Get configuration from environment
        thinking_detail = os.getenv("THINKING_DETAIL_LEVEL", "standard")
        progress_frequency = float(os.getenv("PROGRESS_UPDATE_FREQUENCY", "2.0"))
        max_thinking_steps = int(os.getenv("MAX_THINKING_STEPS", "50"))
        thinking_timeout = float(os.getenv("THINKING_TIMEOUT", "300.0"))
        
        # Determine if we're in debug mode
        debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        
        return ThinkingConfig(
            enable_thinking_stream=True,
            enable_progress_stream=True,
            thinking_detail_level=thinking_detail,
            progress_update_frequency=progress_frequency,
            max_thinking_steps=max_thinking_steps,
            thinking_timeout=thinking_timeout,
            auto_create_session=True,
            session_prefix="ouioe"
        )
    
    @staticmethod
    def create_thinking_client(ollama_host: Optional[str] = None,
                             default_model: Optional[str] = None,
                             thinking_config: Optional[ThinkingConfig] = None) -> ThinkingLLMClient:
        """
        Convenience method to create a thinking-aware LLM client.
        
        Args:
            ollama_host: Ollama server host URL
            default_model: Default model to use
            thinking_config: Configuration for thinking capabilities
            
        Returns:
            ThinkingLLMClient: Thinking-aware LLM client
        """
        return LLMServiceFactory.create_client(
            client_type=LLMClientType.THINKING,
            ollama_host=ollama_host,
            default_model=default_model,
            thinking_config=thinking_config
        )
    
    @staticmethod
    def create_standard_client(ollama_host: Optional[str] = None,
                             default_model: Optional[str] = None) -> LLMEngine:
        """
        Convenience method to create a standard LLM client.
        
        Args:
            ollama_host: Ollama server host URL
            default_model: Default model to use
            
        Returns:
            LLMEngine: Standard LLM client
        """
        return LLMServiceFactory.create_client(
            client_type=LLMClientType.STANDARD,
            ollama_host=ollama_host,
            default_model=default_model
        )
    
    @staticmethod
    def get_client_capabilities(client: Union[LLMEngine, ThinkingLLMClient]) -> Dict[str, Any]:
        """
        Get capabilities information for an LLM client.
        
        Args:
            client: LLM client instance
            
        Returns:
            Dict containing client capabilities
        """
        
        capabilities = {
            "client_type": "thinking" if isinstance(client, ThinkingLLMClient) else "standard",
            "supports_thinking": isinstance(client, ThinkingLLMClient),
            "supports_progress": isinstance(client, ThinkingLLMClient),
            "supports_streaming": isinstance(client, ThinkingLLMClient),
            "methods": []
        }
        
        # Standard methods available in all clients
        standard_methods = ["chat", "generate", "summarize", "analyze", "get_available_models", "pull_model"]
        capabilities["methods"].extend(standard_methods)
        
        # Thinking-specific methods
        if isinstance(client, ThinkingLLMClient):
            thinking_methods = [
                "chat_with_thinking", "generate_with_thinking", 
                "summarize_with_thinking", "analyze_with_thinking",
                "create_thinking_session", "close_thinking_session",
                "get_thinking_session_stats"
            ]
            capabilities["methods"].extend(thinking_methods)
            
            # Add thinking configuration
            if hasattr(client, 'thinking_config'):
                capabilities["thinking_config"] = client.thinking_config.__dict__
        
        return capabilities

# Convenience functions for backward compatibility
def create_llm_client(thinking_enabled: bool = None, **kwargs) -> Union[LLMEngine, ThinkingLLMClient]:
    """
    Create an LLM client with optional thinking capabilities.
    
    Args:
        thinking_enabled: Whether to enable thinking capabilities (None for auto-detect)
        **kwargs: Additional configuration options
        
    Returns:
        LLM client instance
    """
    if thinking_enabled is None:
        client_type = LLMClientType.AUTO
    elif thinking_enabled:
        client_type = LLMClientType.THINKING
    else:
        client_type = LLMClientType.STANDARD
    
    return LLMServiceFactory.create_client(client_type=client_type, **kwargs)

def get_default_llm_client() -> Union[LLMEngine, ThinkingLLMClient]:
    """
    Get a default LLM client based on environment configuration.
    
    Returns:
        LLM client instance
    """
    return LLMServiceFactory.create_client(client_type=LLMClientType.AUTO)
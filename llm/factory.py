"""
LLM Client Factory
Creates the appropriate LLM client based on configuration
"""

import os
from typing import Dict, Any, Optional
from .client import LLMClient
from .ollama_client import OllamaClient
from .vllm_client import VLLMClient


def create_llm_client(config: Optional[Dict[str, Any]] = None) -> LLMClient:
    """
    Create an LLM client based on configuration.
    
    Args:
        config: Optional configuration dictionary. If not provided, uses environment variables.
        
    Returns:
        Configured LLM client instance
        
    Environment Variables:
        LLM_PROVIDER: "ollama" or "vllm" (default: "ollama")
        LLM_BASE_URL: Base URL for the LLM service
        LLM_MODEL: Default model name
        LLM_TIMEOUT: Request timeout in seconds
    """
    if config is None:
        config = {}
    
    # Determine provider from config or environment
    provider = config.get("provider", os.getenv("LLM_PROVIDER", "ollama")).lower()
    
    if provider == "vllm":
        # vLLM configuration
        vllm_config = {
            "base_url": config.get("base_url", os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")),
            "default_model": config.get("default_model", os.getenv("LLM_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ")),
            "timeout": int(config.get("timeout", os.getenv("LLM_TIMEOUT", "60")))
        }
        return VLLMClient(vllm_config)
    
    elif provider == "ollama":
        # Ollama configuration (backward compatibility)
        ollama_config = {
            "base_url": config.get("base_url", os.getenv("OLLAMA_HOST", "http://localhost:11434")),
            "default_model": config.get("default_model", os.getenv("DEFAULT_MODEL", "qwen2.5:7b-instruct-q4_k_m")),
            "timeout": int(config.get("timeout", os.getenv("OLLAMA_TIMEOUT", "180")))
        }
        return OllamaClient(ollama_config)
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported providers: 'ollama', 'vllm'")


def get_default_llm_client() -> LLMClient:
    """
    Get the default LLM client based on environment configuration.
    
    Returns:
        Configured LLM client instance
    """
    return create_llm_client()
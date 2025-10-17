"""
LLM Client Factory
Creates vLLM client for high-performance inference
"""

import os
from typing import Dict, Any, Optional
from .client import LLMClient
from .vllm_client import VLLMClient


def create_llm_client(config: Optional[Dict[str, Any]] = None) -> LLMClient:
    """
    Create a vLLM client based on configuration.
    
    Args:
        config: Optional configuration dictionary. If not provided, uses environment variables.
        
    Returns:
        Configured vLLM client instance
        
    Environment Variables:
        LLM_BASE_URL: Base URL for the vLLM service (default: http://localhost:8000/v1)
        LLM_MODEL: Default model name (default: Qwen/Qwen2.5-7B-Instruct-AWQ)
        LLM_TIMEOUT: Request timeout in seconds (default: 60)
        LLM_MAX_MODEL_LEN: Maximum model length (default: 12288)
        LLM_OUTPUT_RESERVE: Reserved tokens for output (default: 3000)
        LLM_SAFETY_MARGIN: Safety margin tokens (default: 128)
    """
    if config is None:
        config = {}
    
    # vLLM configuration with token budgeting
    vllm_config = {
        "base_url": config.get("base_url", os.getenv("LLM_BASE_URL", "http://localhost:8007/v1")),
        "default_model": config.get("default_model", os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-AWQ")),
        "timeout": int(config.get("timeout", os.getenv("LLM_TIMEOUT", "60"))),
        "max_model_len": int(config.get("max_model_len", os.getenv("LLM_MAX_MODEL_LEN", "12288"))),
        "output_reserve": int(config.get("output_reserve", os.getenv("LLM_OUTPUT_RESERVE", "3000"))),
        "safety_margin": int(config.get("safety_margin", os.getenv("LLM_SAFETY_MARGIN", "128")))
    }
    return VLLMClient(vllm_config)


def get_default_llm_client() -> LLMClient:
    """
    Get the default LLM client based on environment configuration.
    
    Returns:
        Configured LLM client instance
    """
    return create_llm_client()
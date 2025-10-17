"""
LLM Integration Layer
NEWIDEA.MD Pipeline - Large Language Model Integration

This module provides the interface between the pipeline stages and
vLLM backend for high-performance inference.

Key components:
- LLM client abstraction
- Prompt management
- Response parsing
- Error handling and retries
- Model configuration
"""

from .client import LLMClient
from .vllm_client import VLLMClient
from .prompt_manager import PromptManager
from .response_parser import ResponseParser

__all__ = [
    "LLMClient",
    "VLLMClient", 
    "PromptManager",
    "ResponseParser"
]
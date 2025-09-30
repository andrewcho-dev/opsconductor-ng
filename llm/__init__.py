"""
LLM Integration Layer
NEWIDEA.MD Pipeline - Large Language Model Integration

This module provides the interface between the pipeline stages and
various LLM backends (Ollama, OpenAI, etc.).

Key components:
- LLM client abstraction
- Prompt management
- Response parsing
- Error handling and retries
- Model configuration
"""

from .client import LLMClient
from .ollama_client import OllamaClient
from .prompt_manager import PromptManager
from .response_parser import ResponseParser

__all__ = [
    "LLMClient",
    "OllamaClient", 
    "PromptManager",
    "ResponseParser"
]
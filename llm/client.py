"""
LLM Client Abstract Base Class
Defines the interface for all LLM integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class LLMRequest(BaseModel):
    """Request to LLM"""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    model: Optional[str] = None

class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = {}

class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the LLM backend
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the LLM backend"""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from LLM
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with generated content
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if LLM backend is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of model names
        """
        pass

class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass

class LLMConnectionError(LLMError):
    """LLM connection error"""
    pass

class LLMGenerationError(LLMError):
    """LLM generation error"""
    pass
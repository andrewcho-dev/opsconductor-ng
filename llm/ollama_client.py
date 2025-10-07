"""
Ollama LLM Client Implementation
Connects to local Ollama instance for LLM inference
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
import httpx
import json
from .client import LLMClient, LLMRequest, LLMResponse, LLMConnectionError, LLMGenerationError

class OllamaClient(LLMClient):
    """Ollama LLM client implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama2")
        self.timeout = config.get("timeout", 30)
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> bool:
        """Connect to Ollama instance"""
        try:
            # Create client with increased connection limits for parallel LLM calls
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=limits
            )
            
            # Test connection with health check
            is_healthy = await self.health_check()
            self.is_connected = is_healthy
            return is_healthy
            
        except Exception as e:
            self.is_connected = False
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Ollama"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.is_connected = False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Ollama"""
        if not self.is_connected or not self.client:
            raise LLMConnectionError("Not connected to Ollama")
        
        import logging
        logger = logging.getLogger(__name__)
        
        start_time = time.time()
        model = request.model or self.default_model
        prompt_preview = request.prompt[:100] if request.prompt else ""
        
        logger.info(f"🤖 LLM Call starting - Model: {model}, Prompt: {prompt_preview}...")
        
        try:
            # Prepare request payload
            payload = {
                "model": model,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_ctx": 16384,  # Increase context window to 16K tokens
                }
            }
            
            if request.system_prompt:
                payload["system"] = request.system_prompt
            
            if request.max_tokens:
                payload["options"]["num_predict"] = request.max_tokens
            
            # Make request to Ollama
            logger.info(f"📡 Sending request to Ollama at {self.base_url}/api/generate (timeout: {self.timeout}s)")
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            result = response.json()
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ LLM Call complete in {processing_time_ms}ms - Tokens: {result.get('eval_count', 'N/A')}")
            
            return LLMResponse(
                content=result.get("response", ""),
                model=result.get("model", request.model or self.default_model),
                tokens_used=result.get("eval_count"),
                processing_time_ms=processing_time_ms,
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration")
                }
            )
            
        except httpx.TimeoutException as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ LLM Call TIMEOUT after {elapsed}ms - Model: {model}")
            raise LLMGenerationError(f"Ollama timeout after {elapsed}ms: {e}")
        except httpx.HTTPStatusError as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ LLM Call HTTP ERROR after {elapsed}ms - Status: {e.response.status_code}")
            raise LLMGenerationError(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ LLM Call REQUEST ERROR after {elapsed}ms - {str(e)}")
            raise LLMGenerationError(f"Ollama request error: {e}")
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ LLM Call UNKNOWN ERROR after {elapsed}ms - {str(e)}")
            raise LLMGenerationError(f"Ollama generation failed: {e}")
    
    async def health_check(self) -> bool:
        """Check Ollama health"""
        if not self.client:
            return False
        
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models (sync method for now)"""
        # This would need to be implemented as async in a real scenario
        # For now, return common models
        return [
            "llama2",
            "llama2:7b",
            "llama2:13b",
            "codellama",
            "mistral",
            "neural-chat"
        ]
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.client:
            raise LLMConnectionError("Not connected to Ollama")
        
        try:
            payload = {"name": model_name}
            response = await self.client.post("/api/pull", json=payload)
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List installed models
        
        Returns:
            List of model information dictionaries
        """
        if not self.is_connected or not self.client:
            raise LLMConnectionError("Not connected to Ollama")
        
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except Exception as e:
            raise LLMGenerationError(f"Failed to list models: {e}")
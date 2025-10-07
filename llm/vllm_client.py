"""
vLLM Client Implementation
Connects to vLLM OpenAI-compatible API server for high-performance LLM inference
"""

import time
from typing import Dict, Any, List, Optional
import httpx
from .client import LLMClient, LLMRequest, LLMResponse, LLMConnectionError, LLMGenerationError


class VLLMClient(LLMClient):
    """vLLM client implementation using OpenAI-compatible API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8000/v1")
        self.default_model = config.get("default_model", "Qwen/Qwen2.5-7B-Instruct-AWQ")
        self.timeout = config.get("timeout", 60)  # vLLM can be faster, but keep reasonable timeout
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> bool:
        """Connect to vLLM instance"""
        try:
            # Create client with increased connection limits for parallel LLM calls
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=limits,
                headers={"Content-Type": "application/json"}
            )
            
            # Test connection with health check
            is_healthy = await self.health_check()
            self.is_connected = is_healthy
            return is_healthy
            
        except Exception as e:
            self.is_connected = False
            raise LLMConnectionError(f"Failed to connect to vLLM: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from vLLM"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.is_connected = False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using vLLM OpenAI-compatible API"""
        if not self.is_connected or not self.client:
            raise LLMConnectionError("Not connected to vLLM")
        
        import logging
        logger = logging.getLogger(__name__)
        
        start_time = time.time()
        model = request.model or self.default_model
        prompt_preview = request.prompt[:100] if request.prompt else ""
        
        logger.info(f"🚀 vLLM Call starting - Model: {model}, Prompt: {prompt_preview}...")
        
        try:
            # Prepare OpenAI-compatible request payload
            messages = []
            
            # Add system message if provided
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 2000,
                "stream": False
            }
            
            # Make request to vLLM
            logger.info(f"📡 Sending request to vLLM at {self.base_url}/chat/completions (timeout: {self.timeout}s)")
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            result = response.json()
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response content
            content = result["choices"][0]["message"]["content"]
            
            # Extract token usage
            usage = result.get("usage", {})
            tokens_used = usage.get("completion_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            logger.info(f"✅ vLLM Call complete in {processing_time_ms}ms - Tokens: {tokens_used} (prompt: {prompt_tokens}, total: {total_tokens})")
            
            return LLMResponse(
                content=content,
                model=result.get("model", model),
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                metadata={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": tokens_used,
                    "total_tokens": total_tokens,
                    "finish_reason": result["choices"][0].get("finish_reason"),
                    "usage": usage
                }
            )
            
        except httpx.TimeoutException as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ vLLM Call TIMEOUT after {elapsed}ms - Model: {model}")
            raise LLMGenerationError(f"vLLM timeout after {elapsed}ms: {e}")
        except httpx.HTTPStatusError as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ vLLM Call HTTP ERROR after {elapsed}ms - Status: {e.response.status_code}")
            raise LLMGenerationError(f"vLLM HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ vLLM Call REQUEST ERROR after {elapsed}ms - {str(e)}")
            raise LLMGenerationError(f"vLLM request error: {e}")
        except KeyError as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ vLLM Call PARSE ERROR after {elapsed}ms - Missing key: {e}")
            raise LLMGenerationError(f"vLLM response parsing error: {e}")
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"❌ vLLM Call UNKNOWN ERROR after {elapsed}ms - {str(e)}")
            raise LLMGenerationError(f"vLLM generation failed: {e}")
    
    async def health_check(self) -> bool:
        """Check vLLM health"""
        if not self.client:
            return False
        
        try:
            # Try the /health endpoint first (if available)
            try:
                response = await self.client.get("/health", timeout=5.0)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            # Fallback: try /models endpoint
            response = await self.client.get("/models", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available vLLM models"""
        return [
            self.default_model,
            "Qwen/Qwen2.5-7B-Instruct-AWQ",
            "Qwen/Qwen2.5-7B-Instruct"
        ]
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from vLLM
        
        Returns:
            List of model information dictionaries
        """
        if not self.is_connected or not self.client:
            raise LLMConnectionError("Not connected to vLLM")
        
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except Exception as e:
            raise LLMGenerationError(f"Failed to list models: {e}")